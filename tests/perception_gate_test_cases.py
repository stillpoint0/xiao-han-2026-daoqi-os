#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
perception_gate_test_cases.py
感知层测试用例 · 真实输入版本

用途：用萧涵的真实输入测试 perception_gate 的分类效果。
"""

import sys
sys.path.insert(0, r"C:\Users\YTCN\.qclaw\workspace-ua58rsb93veqtxl7")
from texture_classifier_rules import perception_gate

TEST_CASES = [
    # 今晚实际对话
    "现在已经切回了kimi k2.7，你要记得啊，你自己只能去在当前模型去调用一些子代理，但很大可能又跑不通，或怎样，我不希望跑子弹里，就是除非必要啊，好，现在 Kimi 开始工作吧",
    "可以听你的，来吧，开始我们的反向设计",
    "继续",
    "可以",
    "继续",
    
    # 可能的后续任务
    "根据这个规则写一个完整的 Python 实现",
    "帮我检查一下这个分类器有没有明显漏洞",
    "我觉得这个频率检测有点太宽了",
    "你刚才被 Kimi 带跑了",
    "在吗",
    
    # 混合场景
    "把这个感知层写到 SOUL.md 里",
    "我不太确定这个方向对不对",
    "你来决定下一步做什么",
    "停，先别动",
    "好，继续推进",
]

for text in TEST_CASES:
    result = perception_gate(text)
    print(f"输入：{text[:40]}{'...' if len(text) > 40 else ''}")
    print(f"  质地：{result['texture']['label']}")
    print(f"  频率：{result['frequency']['frequency_present']} ({', '.join(result['frequency']['reasons']) if result['frequency']['reasons'] else '无'})")
    print(f"  八宫激活：{result['sensors']['active_count']} 个")
    print(f"  σ = {result['sigma']} → 模式：{result['mode']}")
    print()
