#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
multi_model_pipeline.py
道器操作系统 · 多模型串行协作模块 · v0.1

用途：把复杂任务拆分为多个子任务，每个子任务选择最合适的模型，串行执行，最后聚合结果。

运行方式：
  python multi_model_pipeline.py
"""

import sys
sys.path.insert(0, r"C:\Users\YTCN\.qclaw\workspace-ua58rsb93veqtxl7")

from typing import Dict, Any, List, Callable
from model_router import select_model, MODEL_PROFILES
from error_recovery import call_with_recovery
from cost_monitor import CostMonitor
from session_persistence import SessionState


# 全局状态
COST_MONITOR = CostMonitor()
SESSION_STATE = SessionState()


def estimate_tokens(text: str) -> int:
    """粗略估算 token 数：按中文字符 1 token / 英文字符 0.5 token。"""
    count = 0
    for ch in text:
        if ord(ch) > 127:
            count += 1
        else:
            count += 0.5
    return int(count)


def run_subtask(
    subtask_id: str,
    subtask_name: str,
    prompt: str,
    preferred_model: str = None,
    mode: str = "EXECUTE",
    system_prompt: str = "",
) -> Dict[str, Any]:
    """
    执行一个子任务，选择合适模型，调用并记录成本。

    如果指定了 preferred_model，优先使用；否则根据子任务名称推断任务类型并路由。
    """
    # 选择模型
    if preferred_model and preferred_model in MODEL_PROFILES:
        selected_model = preferred_model
    else:
        # 根据子任务名称推断任务类型
        task_type = "architecture_design" if "设计" in subtask_name else "code_generation" if "代码" in subtask_name or "实现" in subtask_name else "peer_review" if "复核" in subtask_name or "审查" in subtask_name else "fallback"
        route = select_model(task_type, verbose=False)
        selected_model = route["selected_model"]

    # 检查预算
    budget_check = COST_MONITOR.check_budget(estimated_cost=0.01)
    if not budget_check["allowed"]:
        return {
            "subtask_id": subtask_id,
            "subtask_name": subtask_name,
            "model": selected_model,
            "success": False,
            "output": f"[BUDGET_LIMIT] {budget_check['reason']}",
            "cost": 0.0,
        }

    # 设置降级链
    fallback_chain = [selected_model]
    if selected_model == "deepseek-v4-pro":
        fallback_chain = ["deepseek-v4-pro", "deepseek-chat", "deepseek-v4-flash"]
    elif selected_model == "deepseek-v4-flash":
        fallback_chain = ["deepseek-v4-flash", "deepseek-chat"]

    # 调用模型
    result = call_with_recovery(
        model_id=selected_model,
        task=prompt,
        system_prompt=system_prompt,
        fallback_chain=fallback_chain,
        max_retries=1,
        timeout=60,
    )

    # 记录成本
    if result["success"]:
        input_tokens = estimate_tokens(prompt + system_prompt)
        output_tokens = estimate_tokens(result["output"])
        COST_MONITOR.record(
            model_id=result["model_used"],
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            task=subtask_name,
        )

    return {
        "subtask_id": subtask_id,
        "subtask_name": subtask_name,
        "model": result["model_used"],
        "success": result["success"],
        "output": result["output"],
        "error": result.get("error"),
        "fallback_used": result.get("fallback_used", False),
        "cost": COST_MONITOR.total_cost(),
    }


def run_multi_model_pipeline(
    task: str,
    subtasks: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    多模型串行协作主入口。

    subtasks 格式：[
        {"id": "1", "name": "架构设计", "prompt": "...", "model": "deepseek-v4-pro"},
        {"id": "2", "name": "代码实现", "prompt": "...", "model": "deepseek-chat"},
        {"id": "3", "name": "复核", "prompt": "...", "model": "deepseek-v4-flash"},
    ]
    """
    if not subtasks:
        # 默认三阶段：设计 → 实现 → 复核
        subtasks = [
            {
                "id": "1",
                "name": "架构设计",
                "prompt": f"任务：{task}\n\n请从工程角度设计一个简洁的架构方案。要求：\n1. 列出主要模块\n2. 说明模块间关系\n3. 不要写代码，只给设计说明。\n控制在 500 字以内。",
                "model": "deepseek-v4-pro",
            },
            {
                "id": "2",
                "name": "代码实现",
                "prompt": "请基于以下架构设计，用 Python 实现一个最小可运行版本。\n要求：\n1. 代码自包含\n2. 有简要注释\n3. 不要写测试用例\n4. 控制在 300 行以内。",
                "model": "deepseek-chat",
            },
            {
                "id": "3",
                "name": "快速复核",
                "prompt": "请快速检查以下代码是否与上述架构设计一致，指出明显不一致或遗漏。控制在 200 字以内。",
                "model": "deepseek-v4-flash",
            },
        ]

    # 串行执行
    outputs = []
    context = f"原始任务：{task}\n\n"
    for i, st in enumerate(subtasks):
        # 后续子任务可以看到前面所有结果
        if i > 0:
            prev_outputs = "\n\n".join(
                f"【{o['subtask_name']}】\n{o['output'][:1000]}" for o in outputs
            )
            prompt = f"{context}前面已完成的工作：\n\n{prev_outputs}\n\n现在请执行：{st['name']}\n\n{st['prompt']}"
        else:
            prompt = st["prompt"]

        result = run_subtask(
            subtask_id=st["id"],
            subtask_name=st["name"],
            prompt=prompt,
            preferred_model=st.get("model"),
            mode="EXECUTE",
        )
        outputs.append(result)

        if not result["success"]:
            break

    # 保存会话状态
    SESSION_STATE.update(
        last_mode="EXECUTE",
        last_task_summary="multi_model_pipeline",
        last_user_input=task,
        last_selected_model=outputs[-1]["model"] if outputs else None,
        cost_delta=COST_MONITOR.total_cost(),
    )

    return {
        "task": task,
        "subtasks": outputs,
        "total_cost": COST_MONITOR.total_cost(),
        "budget_status": COST_MONITOR.budget_status(),
    }


if __name__ == "__main__":
    # 演示：用多模型协作设计一个"成本监控模块"
    task = "设计并实现一个 Python 成本监控模块，用于记录每次外部 API 调用的成本。"
    print(f"=== 多模型串行协作演示 ===")
    print(f"任务：{task}\n")

    result = run_multi_model_pipeline(task)

    for st in result["subtasks"]:
        print(f"--- {st['subtask_name']}（模型：{st['model']}）---")
        print(st["output"][:800])
        print(f"[成功：{st['success']} | 降级：{st['fallback_used']}]\n")

    print(f"累计成本：{result['total_cost']:.4f} 元")
    print(f"预算状态：{result['budget_status']}")
