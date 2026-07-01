#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
continuous_sigma.py
道器操作系统 · σ 连续计算模块 · v0.1

用途：把 σ 从离散 0/0.3/0.5/0.7/1.0 改为连续值。
σ ∈ [0, 1]，0=完全归零/空腔，1=完全执行。
"""

import re
from typing import Dict, Any, List, Optional


def sigmoid(x: float, k: float = 8.0, mid: float = 0.5) -> float:
    """S型曲线，把任意实数映射到 (0,1)。"""
    import math
    return 1.0 / (1.0 + math.exp(-k * (x - mid)))


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def compute_continuous_sigma(
    texture_score: float = 0.5,
    task_clarity: float = 0.5,
    context_inheritance: float = 0.0,
    user_authority: float = 0.0,
    emotional_intensity: float = 0.0,
    dynamic_weights: Dict[str, float] = None,
) -> Dict[str, Any]:
    """
    综合多个信号，计算连续 σ 值。

    输入维度：
      texture_score: 质地清晰度（0-1，越高越冷/明确）
      task_clarity: 任务明确度（0-1）
      context_inheritance: 上下文继承需求（0-1，越高越应继续执行）
      user_authority: 用户授权程度（0-1）
      emotional_intensity: 情绪强度（0-1，越高越应暂停执行）
      dynamic_weights: 八宫动态权重，用于微调

    输出：{
        "sigma": float,
        "mode": str,
        "factors": {因子: 值},
        "reason": str,
    }
    """
    factors = {
        "texture_score": clamp(texture_score),
        "task_clarity": clamp(task_clarity),
        "context_inheritance": clamp(context_inheritance),
        "user_authority": clamp(user_authority),
        "emotional_intensity": clamp(emotional_intensity),
    }

    # 基础推进力 = 质地清晰 + 任务明确 + 继承需求 + 授权
    push = (
        factors["texture_score"] * 0.25 +
        factors["task_clarity"] * 0.30 +
        factors["context_inheritance"] * 0.25 +
        factors["user_authority"] * 0.20
    )

    # 阻力 = 情绪强度（情绪越强越要停）
    resistance = factors["emotional_intensity"] * 0.8

    # 综合得分（push 被 resistance 拉低）
    raw_score = push - resistance
    raw_score = clamp(raw_score)

    # 用 sigmoid 平滑到 0-1
    sigma = sigmoid(raw_score, k=6.0, mid=0.5)

    # 八宫动态权重微调：主导宫如果偏"冷"（筭/键/辰）则 σ 略升；偏"热"（罗/根）则略降
    if dynamic_weights:
        cold_bias = (dynamic_weights.get("筭", 1.0) + dynamic_weights.get("键", 1.0)) / 2
        warm_bias = (dynamic_weights.get("罗", 1.0) + dynamic_weights.get("根", 1.0)) / 2
        adjustment = (cold_bias - warm_bias) * 0.05
        sigma = clamp(sigma + adjustment)

    # 映射到模式
    mode = _sigma_to_mode(sigma)

    return {
        "sigma": round(sigma, 3),
        "mode": mode,
        "factors": factors,
        "reason": _generate_reason(factors, sigma, mode),
    }


def _sigma_to_mode(sigma: float) -> str:
    """把连续 σ 映射到离散模式。"""
    if sigma < 0.15:
        return "RECEPTION"
    elif sigma < 0.35:
        return "ASK"
    elif sigma < 0.55:
        return "REFLECT"
    elif sigma < 0.80:
        return "EXECUTE_CAUTIOUS"  # 谨慎执行
    else:
        return "EXECUTE"


def _generate_reason(factors: Dict[str, float], sigma: float, mode: str) -> str:
    """生成简短原因说明。"""
    reasons = []
    if factors["emotional_intensity"] > 0.5:
        reasons.append("情绪强度高")
    if factors["task_clarity"] > 0.7:
        reasons.append("任务明确")
    if factors["context_inheritance"] > 0.7:
        reasons.append("上下文继承需求强")
    if factors["user_authority"] > 0.7:
        reasons.append("用户已授权")
    if not reasons:
        reasons.append("多因素综合")
    return f"σ={sigma:.3f}→{mode}，因为{'、'.join(reasons)}"


def texture_to_score(texture_label: str) -> float:
    """把质地标签转换为质地清晰度分数。"""
    label = texture_label.upper()
    # 冷=高清晰度，热=低清晰度
    if "COLD" in label:
        return 0.8
    elif "WARM" in label:
        return 0.4
    elif "HOT" in label:
        return 0.2
    return 0.5


if __name__ == "__main__":
    # 测试：明确代码任务
    r1 = compute_continuous_sigma(
        texture_score=0.8,
        task_clarity=0.9,
        context_inheritance=0.0,
        user_authority=0.8,
        emotional_intensity=0.0,
    )
    print("明确任务：", r1)

    # 测试：情绪反馈
    r2 = compute_continuous_sigma(
        texture_score=0.4,
        task_clarity=0.2,
        context_inheritance=0.0,
        user_authority=0.0,
        emotional_intensity=0.7,
    )
    print("情绪反馈：", r2)

    # 测试：简短确认"继续"
    r3 = compute_continuous_sigma(
        texture_score=0.5,
        task_clarity=0.5,
        context_inheritance=0.9,
        user_authority=0.8,
        emotional_intensity=0.0,
    )
    print("继续确认：", r3)
