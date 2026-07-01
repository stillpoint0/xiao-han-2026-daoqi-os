#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上下文继承测试（context inheritance test）
"""

import sys
sys.path.insert(0, r"C:\Users\YTCN\.qclaw\workspace-ua58rsb93veqtxl7")
from texture_classifier_rules import perception_gate

# 场景：上一轮在执行"反向设计感知层架构"
last_mode = "EXECUTE"
last_summary = "反向设计感知层架构"

follow_ups = ["继续", "可以", "好", "好的", "嗯", "行", "ok"]

for text in follow_ups:
    result = perception_gate(text, last_mode=last_mode, last_task_summary=last_summary)
    inherited = result.get("inherited", False)
    print(f"输入：{text} | σ = {result['sigma']} | 模式：{result['mode']} | 继承：{inherited}")
