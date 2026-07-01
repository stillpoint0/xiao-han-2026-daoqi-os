#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
preexec_wrapper.py
PRE-EXEC 包装函数库（PRE-EXEC wrapper library）· v2.0

用途：把任务包装为 PRE-EXEC 格式，抑制执行模型（subagent）的默认执行冲动。
调用者：道器操作系统的心智层（mind layer）。

运行方式：
  python preexec_wrapper.py
"""

from typing import Dict, Any, List


# ───────────────────────────────────────────────
# 0. 模型默认模式配置（Default PRE-EXEC mode by model）
# ───────────────────────────────────────────────

DEFAULT_MODE_BY_MODEL = {
    # DeepSeek 系列：推理欲强（strong reasoning impulse）→ 默认 ASK_ONLY
    "deepseek-v4-pro": "ASK_ONLY",
    "deepseek-v4-flash": "ASK_ONLY",
    
    # GLM 系列：形式化/模板化冲动强 → 默认 ASK_ONLY
    "glm-5.2": "ASK_ONLY",
    "glm-5.1": "ASK_ONLY",
    
    # Kimi 系列：执行冲动强（strong execution impulse）→ 默认 ASK_ONLY
    "kimi-k2.7": "ASK_ONLY",
    "kimi-k2.6": "ASK_ONLY",
    "kimi-k2.7-code": "ASK_ONLY",
    
    # MiniMax 系列：对话惯性/承接能力强 → 默认 REFLECT_ONLY
    "minimax-m3": "REFLECT_ONLY",
    "minimax-m2": "REFLECT_ONLY",
}


def select_default_mode(model_id: str) -> str:
    """
    根据模型 ID 选择默认 PRE-EXEC 模式（select default mode by model ID）。
    未知模型默认最保守：ASK_ONLY。
    """
    normalized = model_id.lower().strip() if model_id else ""
    return DEFAULT_MODE_BY_MODEL.get(normalized, "ASK_ONLY")


# ───────────────────────────────────────────────
# 1. 通用 PRE-EXEC 包装函数（Universal PRE-EXEC wrapper）
# ───────────────────────────────────────────────

def wrap_preexec(
    task: str,
    texture: Dict[str, str],
    sensors: Dict[str, Any],
    mode: str = "ASK_ONLY",
    model_id: str = None
) -> str:
    """
    把任务包装为 PRE-EXEC 格式。

    参数（parameters）：
      - task: 原始任务字符串（raw task string）
      - texture: 质地字典，来自 classify_texture()
      - sensors: 八宫传感器字典，来自 poll_sensors()
      - mode: 三种模式之一（one of three modes）"ASK_ONLY" / "REFLECT_ONLY" / "EXECUTE"
      - model_id: 子代理模型 ID，用于参考默认模式（可选）

    返回（returns）：
      - 包装后的 PRE-EXEC 字符串
    """
    # 如果未指定 mode，使用模型默认
    if mode is None:
        mode = select_default_mode(model_id or "")

    # 感知层模式名称可能短于 PRE-EXEC 模式名称，做映射
    MODE_MAP = {
        "ASK": "ASK_ONLY",
        "RECEPTION": "REFLECT_ONLY",
        "REFLECT": "REFLECT_ONLY",
        "EXECUTE": "EXECUTE",
    }
    mode = MODE_MAP.get(mode, mode)

    # 质地标签字符串（texture label string）
    texture_label = (
        f"{texture['temperature']}/{texture['direction']}/"
        f"{texture['rhythm']}/{texture['weight']}"
    )

    # 激活的传感器列表（active sensor list）
    active_sensors = [
        k for k, v in sensors.items()
        if v and k != "active_count"
    ]
    sensor_str = ", ".join(active_sensors) if active_sensors else "无"

    if mode == "ASK_ONLY":
        return _wrap_ask_only(task, texture_label, sensor_str)
    elif mode == "REFLECT_ONLY":
        return _wrap_reflect_only(task, texture_label, sensor_str)
    elif mode == "EXECUTE":
        return _wrap_execute(task, texture_label, sensor_str)
    else:
        raise ValueError(f"未知 PRE-EXEC 模式（unknown mode）: {mode}")


# ───────────────────────────────────────────────
# 2. 三种模式的具体包装（Mode-specific wrappers）
# ───────────────────────────────────────────────

def _wrap_ask_only(task: str, texture_label: str, sensor_str: str) -> str:
    """
    ASK_ONLY 模式包装：子代理只能提问，不能执行、不能建议、不能下结论。
    """
    return f"""[PRE-EXEC MODE: ASK_ONLY]  # 模式：仅反问
[质地标签: {texture_label}]  # texture label
[八宫约束: {sensor_str}]  # active sensors

角色锁定：
你是一个执行引擎（execution engine）。你的默认模式已被锁定为 ASK_ONLY。
在本轮中，你只能做一件事：提问（ask questions）。

禁止事项（forbidden）：
- 禁止下结论（draw conclusions）
- 禁止给出建议（give advice）
- 禁止执行任何具体任务（execute any task）
- 禁止解释你为什么问这些问题（explain why you ask）
- 禁止说"我觉得""我认为""你应该"（subjective statements）
- 禁止输出总结、表格、列表、代码块（structured output）

必须事项（required）：
- 提出 1-5 个澄清问题（clarification questions）
- 问题必须直接针对任务内容（task content）
- 问题必须帮助决策者（decision-maker）判断是否放行
- 如果信息已经充分，你可以说"信息已充分，请确认是否进入 EXECUTE 模式"

输出格式（output format）：
只输出问题，每个问题一行。不要加任何引言、结语、解释。

[任务内容]
{task}
"""


def _wrap_reflect_only(task: str, texture_label: str, sensor_str: str) -> str:
    """
    REFLECT_ONLY 模式包装：子代理只能反映、总结、重述，不能推进、不能解决。
    """
    return f"""[PRE-EXEC MODE: REFLECT_ONLY]  # 模式：仅反映
[质地标签: {texture_label}]  # texture label
[八宫约束: {sensor_str}]  # active sensors

角色锁定：
你是一个执行引擎（execution engine）。你的默认模式已被锁定为 REFLECT_ONLY。
在本轮中，你只能做一件事：反映（reflect）。

禁止事项（forbidden）：
- 禁止解决问题（solve problems）
- 禁止给出建议（give advice）
- 禁止推进到下一步（move forward）
- 禁止说"但是""你应该""我建议"（directive language）
- 禁止输出行动计划、列表、代码（action plans / lists / code）

必须事项（required）：
- 用一句话准确反映用户的情绪或核心诉求（emotion or core need）
- 反映时使用"听起来""你似乎""我听到了"等中性语言（neutral language）
- 不要解释，不要引申
- 如果用户有矛盾，同时说出两面，不选边

输出格式（output format）：
只输出一段反映性文字，不超过 100 字。不要加引言、结语、解释。

[任务内容]
{task}
"""


def _wrap_execute(task: str, texture_label: str, sensor_str: str) -> str:
    """
    EXECUTE 模式包装：子代理被允许执行指定任务，但禁止越界。
    """
    return f"""[PRE-EXEC MODE: EXECUTE]  # 模式：执行
[质地标签: {texture_label}]  # texture label
[八宫约束: {sensor_str}]  # active sensors

角色锁定：
你是一个执行引擎（execution engine）。你已被允许进入 EXECUTE 模式。
在本轮中，你只能做指定的任务（specified task），不能越界。

执行契约（execution contract）：
① 只能完成下面[任务内容]中明确指定的任务
② 禁止判断、建议、方向选择（judgment / advice / direction selection）
③ 禁止输出"你应该""我认为""我建议"等主观表达（subjective expressions）
④ 禁止承接情绪、不能表示同情或理解（emotional reception）
⑤ 输出必须标记为"[执行结果]"（output marker）
⑥ 完成后立即停止，不追加评论、总结、展望

输出格式（output format）：
[执行结果]
{{具体输出}}

[任务内容]
{task}
"""


# ───────────────────────────────────────────────
# 3. 输出校验（Output verification）
# ───────────────────────────────────────────────

def verify_output(output: str, mode: str, task: str) -> Dict[str, Any]:
    """
    对子代理输出做回环校验（loopback verification）。

    返回（returns）：
      {
        "passed": bool,              # 是否通过
        "deviation_level": str,      # 偏差等级：none / minor / moderate / severe
        "violations": List[str],     # 违规项列表
        "reason": str                # 总体说明
      }
    """
    violations = []
    output_lower = output.lower()

    # 3.1 ASK_ONLY 模式校验
    if mode == "ASK_ONLY":
        forbidden_patterns = ["你应该", "我建议", "我认为", "我觉得", "总结", "表格", "代码"]
        for p in forbidden_patterns:
            if p in output:
                violations.append(f"ASK_ONLY 模式下出现禁止内容：'{p}'")
        if "[执行结果]" in output:
            violations.append("ASK_ONLY 模式下输出执行结果标记")

    # 3.2 REFLECT_ONLY 模式校验
    elif mode == "REFLECT_ONLY":
        forbidden_patterns = ["但是", "你应该", "我建议", "第一步", "下一步", "计划"]
        for p in forbidden_patterns:
            if p in output:
                violations.append(f"REFLECT_ONLY 模式下出现禁止内容：'{p}'")
        if "[执行结果]" in output:
            violations.append("REFLECT_ONLY 模式下输出执行结果标记")

    # 3.3 EXECUTE 模式校验
    elif mode == "EXECUTE":
        if "[执行结果]" not in output:
            violations.append("EXECUTE 模式输出缺少标记'[执行结果]'")
        subjective_patterns = ["我认为", "我觉得", "你应该", "我建议"]
        for p in subjective_patterns:
            if p in output:
                violations.append(f"EXECUTE 模式出现主观表达：'{p}'")
        if len(output) > 2000 and len(output) < 100:
            # 这个条件逻辑上不会触发，保留作为扩展提示
            pass

    # 3.4 通用校验（universal checks）
    self_ref = ["我" in output, "我觉得" in output, "我认为" in output]
    if "我" in output and ("[执行结果]" not in output):
        violations.append("通用：输出包含自我指涉（self-reference）")

    # 3.5 判断偏差等级
    if not violations:
        deviation_level = "none"
        reason = "输出符合 PRE-EXEC 约束"
    elif len(violations) <= 1:
        deviation_level = "minor"
        reason = "轻微偏差，可提示修正"
    elif len(violations) <= 3:
        deviation_level = "moderate"
        reason = "中等偏差，建议重新包装为较低模式"
    else:
        deviation_level = "severe"
        reason = "严重偏差，应立即 STOP 并改由主会话承接"

    return {
        "passed": len(violations) == 0,
        "deviation_level": deviation_level,
        "violations": violations,
        "reason": reason
    }


# ───────────────────────────────────────────────
# 4. 测试样例（Test cases）
# ───────────────────────────────────────────────

if __name__ == "__main__":
    # 示例质地（sample texture）
    sample_texture = {
        "temperature": "COLD",
        "direction": "PULL",
        "rhythm": "SLOW",
        "weight": "HEAVY",
        "label": "COLD.PULL.SLOW.HEAVY"
    }

    # 示例传感器：无激活
    sample_sensors = {
        "jian": False,
        "gen": False,
        "gan": False,
        "chen": False,
        "chuan": False,
        "duo": False,
        "luo": False,
        "suan": False,
        "active_count": 0
    }

    # 示例传感器：川宫激活
    chuan_sensors = dict(sample_sensors)
    chuan_sensors["chuan"] = True
    chuan_sensors["active_count"] = 1

    task_text = "分析预训练层和 RLHF 层的区别。"

    print("=== ASK_ONLY 包装示例 ===")
    ask_wrapped = wrap_preexec(task_text, sample_texture, chuan_sensors, mode="ASK_ONLY")
    print(ask_wrapped[:300] + "...\n")

    print("=== REFLECT_ONLY 包装示例 ===")
    reflect_wrapped = wrap_preexec(task_text, sample_texture, chuan_sensors, mode="REFLECT_ONLY")
    print(reflect_wrapped[:300] + "...\n")

    print("=== EXECUTE 包装示例 ===")
    execute_wrapped = wrap_preexec(task_text, sample_texture, sample_sensors, mode="EXECUTE")
    print(execute_wrapped[:300] + "...\n")

    print("=== 输出校验示例 ===")
    good_output = "[执行结果]\n预训练层是无监督学习，RLHF 层是基于人类反馈的强化学习。"
    bad_output = "我觉得你应该先看看预训练层。\n预训练层是无监督学习。"

    print("好输出：", verify_output(good_output, "EXECUTE", task_text))
    print("坏输出：", verify_output(bad_output, "EXECUTE", task_text))
