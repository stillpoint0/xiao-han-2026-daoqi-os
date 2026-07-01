#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
perception_gate_dynamic_test.py
道器操作系统 · 感知层动态模式测试 · v0.1

用途：对比经典离散 σ 与动态连续 σ 的输出差异。
"""

import sys
sys.path.insert(0, r"C:\Users\YTCN\.qclaw\workspace-ua58rsb93veqtxl7")

from texture_classifier_rules import perception_gate


TEST_CASES = [
    {
        "name": "明确代码任务",
        "input": "帮我用 Python 实现一个质地分类器",
        "last_mode": None,
        "task_type": "code_generation",
        "rhythm": "steady",
    },
    {
        "name": "执行后简短确认",
        "input": "继续",
        "last_mode": "EXECUTE",
        "task_type": "code_generation",
        "rhythm": "fast",
    },
    {
        "name": "情绪反馈",
        "input": "我觉得这个方向不对",
        "last_mode": "EXECUTE",
        "task_type": "code_generation",
        "rhythm": "pause",
    },
    {
        "name": "质疑方向",
        "input": "你刚才被 Kimi 带跑了",
        "last_mode": None,
        "task_type": None,
        "rhythm": "drift",
    },
    {
        "name": "甩责任",
        "input": "你决定下一步做什么",
        "last_mode": None,
        "task_type": None,
        "rhythm": "steady",
    },
    {
        "name": "复杂架构任务",
        "input": "反向设计感知层架构，先做模型路由层",
        "last_mode": None,
        "task_type": "architecture_design",
        "rhythm": "steady",
    },
]

if __name__ == "__main__":
    print("=== 感知层动态模式对比测试 ===\n")
    for case in TEST_CASES:
        print(f"【{case['name']}】输入：{case['input']}")

        classic = perception_gate(
            case["input"],
            last_mode=case.get("last_mode"),
            dynamic=False,
        )
        dynamic = perception_gate(
            case["input"],
            last_mode=case.get("last_mode"),
            dynamic=True,
            task_type=case.get("task_type"),
            rhythm=case.get("rhythm", "steady"),
        )

        print(f"  经典模式：σ={classic['sigma']} → {classic['mode']}")
        print(f"  动态模式：σ={dynamic['sigma']} → {dynamic['mode']}")
        if "dynamic_weights" in dynamic:
            print(f"  主导宫：{dynamic['dynamic_weights']['dominant']}")
        print(f"  原因：{dynamic.get('reason', 'N/A')}")
        print()
