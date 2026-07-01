#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
end_to_end_pipeline.py
道器操作系统 · 端到端流程（End-to-End Pipeline）· v2.0

用途：
  1. 感知层判断
  2. 模型路由选择
  3. PRE-EXEC 包装
  4. 外部模型调用（带错误恢复与降级）
  5. 成本监控
  6. 输出校验
  7. 会话状态持久化

运行方式：
  python end_to_end_pipeline.py
"""

import sys
sys.path.insert(0, r"C:\Users\YTCN\.qclaw\workspace-ua58rsb93veqtxl7")

from texture_classifier_rules import perception_gate
from model_router import select_model, infer_task_type
from preexec_wrapper import wrap_preexec, verify_output
from cost_monitor import CostMonitor
from error_recovery import call_with_recovery, fallback_to_local
from session_persistence import SessionState

from typing import Dict, Any


# 全局状态：成本监控 + 会话持久化
COST_MONITOR = CostMonitor()
SESSION_STATE = SessionState()


# ───────────────────────────────────────────────
# 0. 端到端流程函数
# ───────────────────────────────────────────────

def run_pipeline(
    user_input: str,
    last_mode: str = None,
    last_task_summary: str = None,
    available_models: list = None
) -> Dict[str, Any]:
    """
    端到端流程：
      1. 感知层（perception gate）
      2. 模型路由（model router，仅 EXECUTE 模式）
      3. 降级警告
      4. PRE-EXEC 包装
      5. 真实子代理输出（带错误恢复 + 预算控制）
      6. 输出校验
      7. 会话状态持久化
    """
    # 步骤1：感知层
    perception = perception_gate(user_input, last_mode, last_task_summary)
    mode = perception["mode"]
    texture = perception["texture"]
    sensors = perception["sensors"]

    # 步骤2：模型路由（仅 EXECUTE 模式需要）
    routing = None
    degrade_warning = None
    task_type = None
    if mode == "EXECUTE":
        task_type = infer_task_type(user_input)
        routing = select_model(task_type, available_models=available_models, verbose=True)

        # 步骤3：降级警告
        if routing["score"] < 0.3:
            degrade_warning = (
                f"⚠️ 严重降级警告：当前最佳模型 '{routing['selected_model']}' "
                f"对此任务的匹配分数仅 {routing['score']:.3f}，远低于可用阈值。"
                f"建议：使用主会话模型（Kimi K2.7）处理，或确认是否继续用本地模型。"
            )
        elif routing["fallback"]:
            degrade_warning = (
                f"⚠️ 降级提示：当前模型 '{routing['selected_model']}' "
                f"对此任务的匹配分数为 {routing['score']:.3f}，属于降级方案。"
            )

    # 步骤4：PRE-EXEC 包装
    model_id = routing["selected_model"] if routing else None
    wrapped = wrap_preexec(
        task=user_input,
        texture=texture,
        sensors=sensors,
        mode=mode if mode in ("ASK_ONLY", "REFLECT_ONLY", "EXECUTE") else "ASK_ONLY",
        model_id=model_id
    )

    # 步骤5：真实子代理输出（带错误恢复 + 预算检查）
    real_output = run_subagent(mode, model_id, wrapped, system_prompt=wrapped, user_input=user_input)

    # 步骤6：输出校验
    verification = verify_output(real_output, mode, user_input)

    # 步骤7：会话状态持久化
    cost_delta = 0.0
    if real_output and not real_output.startswith("["):
        # 粗略估算成本
        cost_delta = len(real_output) / 4000.0 * 0.002
    SESSION_STATE.update(
        last_mode=mode,
        last_task_summary=task_type if routing else "",
        last_user_input=user_input,
        last_selected_model=model_id,
        cost_delta=cost_delta,
    )

    return {
        "input": user_input,
        "perception": perception,
        "routing": routing,
        "degrade_warning": degrade_warning,
        "wrapped_length": len(wrapped),
        "real_output": real_output,
        "verification": verification,
        "cost_status": COST_MONITOR.budget_status(),
    }


def run_subagent(mode: str, model_id: str, task: str, system_prompt: str = "", user_input: str = "") -> str:
    """
    真实子代理输出：本地模型用模拟，DeepSeek 用 API 调用，失败时自动降级。
    """
    if not model_id or model_id == "qwen3.5:9b":
        # 本地/兜底模型仍用模拟
        if mode == "ASK_ONLY":
            return (
                "1. 你想继续哪个方向？\n"
                "2. 这个方向是否有约束条件？\n"
                "3. 你希望我以什么形式回复？"
            )
        elif mode == "REFLECT_ONLY":
            return "听起来，你有些不确定，想让我陪你停一下。"
        elif mode == "EXECUTE":
            return "[执行结果]\n已生成质地分类器的 Python 实现。\n（由于本地模型能力有限，建议后续用更强模型复核）"
        else:
            return "（无输出）"

    # 检查预算
    budget_check = COST_MONITOR.check_budget(estimated_cost=0.01)
    if not budget_check["allowed"]:
        return f"[BUDGET_LIMIT] {budget_check['reason']}"

    # DeepSeek 系列真实调用，带降级链
    if model_id.startswith("deepseek-"):
        fallback_chain = [model_id]
        if model_id == "deepseek-v4-pro":
            fallback_chain = ["deepseek-v4-pro", "deepseek-chat", "deepseek-v4-flash"]
        elif model_id == "deepseek-v4-flash":
            fallback_chain = ["deepseek-v4-flash", "deepseek-chat"]

        result = call_with_recovery(
            model_id=model_id,
            task=task,
            system_prompt=system_prompt,
            fallback_chain=fallback_chain,
            max_retries=1,
            timeout=60
        )

        if result["success"]:
            input_tokens = len(system_prompt) + len(user_input)
            output_tokens = len(result["output"])
            COST_MONITOR.record(
                model_id=result["model_used"],
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                task=user_input
            )
            return result["output"]
        else:
            local = fallback_to_local(task, mode)
            return local["output"]

    return f"[ERROR] 未知模型 {model_id}"


# ───────────────────────────────────────────────
# 1. 测试样例
# ───────────────────────────────────────────────

TEST_CASES = [
    {
        "name": "明确任务",
        "input": "帮我用 Python 实现一个质地分类器",
        "last_mode": None,
        "last_summary": None,
    },
    {
        "name": "执行后确认",
        "input": "继续",
        "last_mode": "EXECUTE",
        "last_summary": "实现质地分类器",
    },
    {
        "name": "情绪反馈",
        "input": "我觉得这个方向不对",
        "last_mode": None,
        "last_summary": None,
    },
    {
        "name": "关系性探询",
        "input": "你刚才被 Kimi 带跑了",
        "last_mode": None,
        "last_summary": None,
    },
    {
        "name": "甩责任",
        "input": "你决定下一步做什么",
        "last_mode": None,
        "last_summary": None,
    },
    {
        "name": "纯问候",
        "input": "在吗",
        "last_mode": None,
        "last_summary": None,
    },
    {
        "name": "复杂架构任务",
        "input": "反向设计感知层架构，先做模型路由层",
        "last_mode": None,
        "last_summary": None,
    },
]

if __name__ == "__main__":
    print("=== 道器操作系统 · 端到端流程测试 v2.0 ===\n")

    for case in TEST_CASES:
        print(f"【{case['name']}】输入：{case['input']}")
        result = run_pipeline(
            case["input"],
            last_mode=case["last_mode"],
            last_task_summary=case["last_summary"]
        )

        p = result["perception"]
        print(f"  感知层：σ={p['sigma']} | 模式={p['mode']} | 质地={p['texture']['label']}")
        if result["routing"]:
            r = result["routing"]
            print(f"  路由层：模型={r['selected_model']} | 分数={r['score']} | 降级={r['fallback']}")
            if result["degrade_warning"]:
                print(f"  {result['degrade_warning']}")
        else:
            print(f"  路由层：未启用（模式={p['mode']}）")

        print(f"  包装长度：{result['wrapped_length']} 字符")
        print(f"  真实输出：{result['real_output'][:80]}{'...' if len(result['real_output'])>80 else ''}")

        v = result["verification"]
        print(f"  校验结果：通过={v['passed']} | 偏差等级={v['deviation_level']}")
        if v["violations"]:
            print(f"  违规项：{v['violations']}")
        print(f"  预算状态：已用 {result['cost_status']['total_cost']:.4f} / {result['cost_status']['budget']:.2f} 元")
        print()

    print("\n=== 会话持久化状态 ===")
    print(SESSION_STATE.get())
