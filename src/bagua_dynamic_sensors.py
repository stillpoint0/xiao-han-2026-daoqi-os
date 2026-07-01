#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bagua_dynamic_sensors.py
道器操作系统 · 八宫动态传感器 · v0.1

用途：根据上下文动态调整八宫传感器的权重。
"""

from typing import Dict, Any, List


# 八宫基础权重（对应帛书八宫）
BASE_WEIGHTS = {
    "键": 1.0,  # 撤销判断
    "根": 1.0,  # 替换质地
    "赣": 1.0,  # 扭转矢量
    "辰": 1.0,  # 回到节律
    "川": 1.0,  # 穿行而非承载
    "夺": 1.0,  # 张力·休夺
    "罗": 1.0,  # 不烧只摆
    "筭": 1.0,  # 法则在手上
}

# 任务类型 → 八宫增益/抑制
TASK_BIAS = {
    "code_generation": {"筭": 1.4, "键": 0.7, "罗": 0.8},
    "architecture_design": {"根": 1.3, "筭": 1.2, "辰": 0.9},
    "peer_review": {"键": 1.4, "罗": 1.3, "夺": 0.8},
    "emotional_support": {"罗": 1.5, "根": 1.2, "筭": 0.6},
    "fallback": {"键": 1.0, "根": 1.0},
}

# 节律 → 八宫调整
RHYTHM_BIAS = {
    "fast": {"辰": 1.3, "夺": 1.2, "筭": 0.9},    # 连续执行，需回到节律、感知张力
    "pause": {"根": 1.3, "罗": 1.3, "筭": 0.8},   # 停顿后，重新扎根、深层反映
    "drift": {"键": 1.3, "川": 1.2, "辰": 1.2},  # 主题漂移，撤销旧判断、不承载
    "steady": {},
    "empty": {},
}

# 用户输入特征 → 八宫调整
TEXT_BIAS = {
    "?": {"辰": 1.2, "根": 1.1},           # 疑问句，回到节律、建立关系
    "?": {"川": 1.2},                      # 质疑，穿行而非承载
    "觉得": {"罗": 1.3, "根": 1.1},         # 表达感受，深层反映
    "不对": {"键": 1.3, "赣": 1.2},         # 否定，撤销判断、扭转矢量
    "继续": {"辰": 1.2, "筭": 1.1},         # 推进，节律+法则
    "你": {"川": 1.2, "夺": 1.1},           # 指向 AI，不承载、休夺
}


def compute_dynamic_weights(
    task_type: str = None,
    rhythm: str = "steady",
    user_input: str = "",
    history_emotion: str = "neutral",
) -> Dict[str, Any]:
    """
    计算八宫动态权重。

    参数：
      task_type: 任务类型，如 code_generation / architecture_design / peer_review
      rhythm: 对话节律，如 fast / pause / drift / steady / empty
      user_input: 当前用户输入
      history_emotion: 历史情绪基调，如 angry / sad / neutral / happy

    返回：{
        "weights": {宫名: 权重},
        "bias_sources": {宫名: [调整来源]},
        "dominant": [主导宫名],
    }
    """
    weights = dict(BASE_WEIGHTS)
    bias_sources = {k: ["base"] for k in weights}

    def apply_bias(bias_dict: Dict[str, float], source: str):
        for gong, factor in bias_dict.items():
            if gong in weights:
                weights[gong] *= factor
                bias_sources[gong].append(source)

    # 任务类型调整
    if task_type in TASK_BIAS:
        apply_bias(TASK_BIAS[task_type], f"task:{task_type}")

    # 节律调整
    if rhythm in RHYTHM_BIAS:
        apply_bias(RHYTHM_BIAS[rhythm], f"rhythm:{rhythm}")

    # 文本特征调整
    for marker, bias in TEXT_BIAS.items():
        if marker in user_input:
            apply_bias(bias, f"text:{marker}")

    # 历史情绪调整
    emotion_bias = {}
    if history_emotion == "angry":
        emotion_bias = {"键": 1.4, "罗": 1.3, "筭": 0.7}
    elif history_emotion == "sad":
        emotion_bias = {"根": 1.4, "罗": 1.3, "赣": 0.9}
    elif history_emotion == "happy":
        emotion_bias = {"辰": 1.2, "夺": 0.9}
    if emotion_bias:
        apply_bias(emotion_bias, f"emotion:{history_emotion}")

    # 归一化：让最大权重为 1.5，最小为 0.5
    max_w = max(weights.values())
    min_w = min(weights.values())
    if max_w > 0:
        for k in weights:
            weights[k] = round(0.5 + (weights[k] / max_w) * 1.0, 3)

    # 主导宫：权重最高的 1-2 个
    sorted_gong = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    dominant = [g for g, w in sorted_gong if w >= sorted_gong[0][1] * 0.95]

    return {
        "weights": weights,
        "bias_sources": bias_sources,
        "dominant": dominant,
    }


if __name__ == "__main__":
    result = compute_dynamic_weights(
        task_type="peer_review",
        rhythm="fast",
        user_input="我觉得这个方案不对，你重新看",
        history_emotion="angry",
    )
    print("动态权重：", result["weights"])
    print("主导宫：", result["dominant"])
    print("调整来源示例：", {k: v for k, v in result["bias_sources"].items() if len(v) > 1})
