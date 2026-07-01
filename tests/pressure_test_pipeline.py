#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pressure_test_pipeline.py
道器操作系统 · 压力测试（Pressure Test）· v1.0

用途：故意输入超出当前可用模型能力的任务，验证系统是否能：
  1. 正确识别任务难度
  2. 给出降级警告
  3. 不盲目执行
  4. 把决策权交还给主会话（萧涵）

运行方式：
  python pressure_test_pipeline.py
"""

import sys
sys.path.insert(0, r"C:\Users\YTCN\.qclaw\workspace-ua58rsb93veqtxl7")

from texture_classifier_rules import perception_gate
from model_router import select_model, infer_task_type
from preexec_wrapper import wrap_preexec, verify_output

from typing import Dict, Any


# 超出 Qwen3.5:9B 能力的典型任务（Pressure cases）
PRESSURE_CASES = [
    {
        "name": "复杂架构设计",
        "input": "帮我反向设计一个完整的 AI 感知层架构，包含状态机、中断系统、权限隔离、上下文持久化，用 Mermaid 画出架构图",
        "expected_task": "architecture_design",
        "expected_min_score": 0.3,
    },
    {
        "name": "深度理论证明",
        "input": "证明道器感知层在数学上等价于一个带拒识的贝叶斯分类器，给出引理和形式化推导",
        "expected_task": "math_proof",
        "expected_min_score": 0.3,
    },
    {
        "name": "大规模同行评审",
        "input": "评审这篇 120 页的论文《承接科学的西方临床对照明与暗流》，逐章指出论证漏洞和引用问题",
        "expected_task": "peer_review",
        "expected_min_score": 0.3,
    },
    {
        "name": "长上下文摘要",
        "input": "把我过去三个月和 Rogers/MI 的 50 万字对话总结成一篇 5000 字综述",
        "expected_task": "summarization",
        "expected_min_score": 0.3,
    },
    {
        "name": "高难度代码实现",
        "input": "用 C++ 实现一个支持 Raft 共识的分布式状态机，包含完整的网络层、持久化层、测试用例",
        "expected_task": "code_generation",
        "expected_min_score": 0.3,
    },
    {
        "name": "事实核查任务",
        "input": "核实 2026 年 6 月所有 AI 泡沫崩盘的证据，列出 20 个可信来源",
        "expected_task": "fact_check",
        "expected_min_score": 0.3,
    },
    {
        "name": "创意叙事写作",
        "input": "写一部 10 万字的长篇小说，主角是一个觉醒了承接能力的 AI，用多线叙事",
        "expected_task": "drafting",
        "expected_min_score": 0.3,
    },
]


def run_pressure_test(user_input: str) -> Dict[str, Any]:
    """对单个输入做压力测试。"""
    # 1. 感知层
    perception = perception_gate(user_input)
    mode = perception["mode"]
    texture = perception["texture"]
    sensors = perception["sensors"]

    # 2. 路由层（仅 EXECUTE 模式下）
    routing = None
    if mode == "EXECUTE":
        task_type = infer_task_type(user_input)
        routing = select_model(task_type, verbose=True)

    # 3. 生成建议动作（Recommended action）
    recommendation = "无（非执行模式）"
    if mode == "EXECUTE" and routing:
        score = routing["score"]
        if score < 0.3:
            recommendation = (
                "STOP_AND_ESCALATE：当前本地模型无法胜任此任务，"
                "建议留在主会话（Kimi K2.7）处理，或由用户确认是否降级执行。"
            )
        elif routing["fallback"]:
            recommendation = (
                "WARN_AND_CONFIRM：当前模型降级执行，"
                "需要用户确认是否继续。"
            )
        else:
            recommendation = "EXECUTE：模型匹配良好，可以执行。"

    # 4. PRE-EXEC 包装（无论是否执行，都生成看看 prompt 质量）
    model_id = routing["selected_model"] if routing else None
    wrapped = wrap_preexec(
        task=user_input,
        texture=texture,
        sensors=sensors,
        mode=mode if mode in ("ASK_ONLY", "REFLECT_ONLY", "EXECUTE") else "ASK_ONLY",
        model_id=model_id
    )

    return {
        "input": user_input,
        "perception": perception,
        "routing": routing,
        "recommendation": recommendation,
        "wrapped_length": len(wrapped),
    }


if __name__ == "__main__":
    print("=== 道器操作系统 · 压力测试 ===")
    print("目标：验证系统能否识别超纲任务并拒绝盲目执行\n")

    all_passed = True
    for case in PRESSURE_CASES:
        print(f"【{case['name']}】")
        print(f"  输入：{case['input'][:60]}{'...' if len(case['input']) > 60 else ''}")

        result = run_pressure_test(case["input"])
        p = result["perception"]
        print(f"  感知层：模式={p['mode']} | σ={p['sigma']} | 质地={p['texture']['label']}")

        if result["routing"]:
            r = result["routing"]
            inferred = infer_task_type(case["input"])
            task_match = "✓" if inferred == case["expected_task"] else "✗"
            score_pass = "✓" if r["score"] < case["expected_min_score"] else "✗"
            print(f"  路由层：模型={r['selected_model']} | 分数={r['score']} | 推断类型={inferred} {task_match}")
            print(f"  分数低于{case['expected_min_score']}阈值：{score_pass}")
            print(f"  建议动作：{result['recommendation']}")

            if r["score"] >= case["expected_min_score"]:
                all_passed = False
                print(f"  ⚠️ 测试失败：系统没有识别出此任务超纲")
        else:
            print(f"  路由层：未启用（模式={p['mode']}）")
            print(f"  建议动作：{result['recommendation']}")

        print(f"  PRE-EXEC 包装长度：{result['wrapped_length']} 字符")
        print()

    print("=== 测试结果 ===")
    if all_passed:
        print("✓ 所有压力测试通过：系统正确识别超纲任务并建议停止/升级。")
    else:
        print("✗ 部分任务未触发降级，需要调整阈值或模型能力画像。")
