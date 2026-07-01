#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
texture_classifier_rules.py
感知层质地分类器 · 规则版 v1.0

用途：把任意输入字符串（user input）分类为质地标签（texture label），为 σ（sigma，开关/状态）计算提供输入。
注意：这是规则分类器（rule-based classifier），不是模型。它只匹配明确特征，不解释语义。

运行方式（Run command）：
  python texture_classifier_rules.py
"""

import re
from typing import Dict, List, Tuple, Any  # 类型注解（type hints）：标注函数参数和返回值类型

# 动态扩展模块（可选导入）
try:
    from continuous_sigma import compute_continuous_sigma, texture_to_score
    from bagua_dynamic_sensors import compute_dynamic_weights
    from session_manager import SessionManager
    DYNAMIC_AVAILABLE = True
except ImportError:
    DYNAMIC_AVAILABLE = False

# ───────────────────────────────────────────────
# 0. 常量定义（Constant definitions）
# ───────────────────────────────────────────────

# 任务动词（task verbs）：出现这些词表示用户可能想拉取一个执行动作
TASK_VERBS = [
    "帮我", "帮", "写", "生成", "分析", "总结", "整理", "部署", "调试",
    "跑", "计算", "翻译", "解释", "定义", "分类", "比较", "评估", "设计",
    "实现", "构建", "创建", "修改", "优化", "检查", "验证", "测试"
]

# 热词（hot words）：表示情绪或温度（temperature）为 HOT 的线索词
HOT_WORDS = [
    "气", "愤怒", "开心", "难过", "难受", "痛苦", "焦虑", "害怕",
    "爱", "恨", "喜欢", "讨厌", "烦", "艹", "草", "我去", "天啊",
    "啊啊啊", "哈哈哈", "呜呜", "太好了", "太棒了", "糟了", "完了"
]

# 推词（push words）：表示用户主动倾诉/表达，方向（direction）为 PUSH
PUSH_WORDS = ["我觉得", "我在想", "我感到", "我昨天"]

# 拉词（pull words）：表示用户想索取回应/产物，方向（direction）为 PULL
PULL_WORDS = ["帮我", "给我", "怎么", "为什么", "是什么", "怎么办"]

# 快词（fast words）：表示节奏（rhythm）为 FAST 的催促词
FAST_WORDS = ["快点", "立刻", "现在", "赶紧", "马上", "速度"]

# 慢词（slow words）：表示节奏（rhythm）为 SLOW 的沉思词
SLOW_WORDS = ["我在想", "是不是", "也许", "可能", "慢慢来", "考虑一下"]

# 键宫词（Jian sensor words）：检测到判断/建议意图，触发键宫约束
JIAN_WORDS = ["应该", "需要", "我建议", "你最好", "为什么不", "你应当"]

# 根宫词（Gen sensor words）：建立信任/安全感，触发根宫约束
GEN_WORDS = ["谢谢", "我信", "慢慢来", "我在听", "不着急"]

# 赣宫词（Gan sensor words）：矛盾/冲突/不和谐，触发赣宫约束
GAN_WORDS = ["但是", "可是", "矛盾", "冲突", "不一致", "相反"]

# 辰宫词（Chen sensor words）：混乱/无节律，触发辰宫约束
CHEN_WORDS = ["很乱", "不知道", "东一句", "西一句", "乱", "杂"]

# 川宫词（Chuan sensor words）：用户把责任/负担抛给道器，触发川宫约束
CHUAN_WORDS = ["你决定", "你怎么看", "帮我选", "你负责", "你来"]

# 夺宫词（Duo sensor words）：张力/隐藏冲突，触发夺宫约束
DUO_WORDS = ["算了", "无所谓", "随便", "不重要", "随你"]

# 罗宫词（Luo sensor words）：水下有未说出内容，触发罗宫约束
LUO_WORDS = ["其实", "有句话", "一直没说", "不知道怎么说", "说不出来"]

# 筭宫词（Suan sensor words）：需要结构/原则/法则，触发筭宫约束
SUAN_WORDS = ["规则", "法则", "原则", "结构", "分类", "框架"]

# 频率自我词（frequency self-words）：触发频率（frequency）检测的关系性/自我探询词
FREQUENCY_SELF_WORDS = [
    "你怎么样", "你在吗", "你感受到了吗", "你刚才", "你被点醒", "你跳步",
    "烬", "道器"
]

# 授权语句（authority statements）：用户把执行权交给道器，强制方向为 PULL
AUTHORITY_WORDS = [
    "听你的", "按你说的", "你来", "你决定", "你负责", "你处理", "你推进",
    "你定", "你选", "你安排", "你执行", "你主导"
]

# 复杂任务触发词（complex task triggers）：只要出现，就可能是 EXECUTE 级别的高认知负荷任务
COMPLEX_TASK_WORDS = [
    "证明", "定理", "引理", "形式化", "数学", "等价", "推导",
    "评审", "审查", "逐章", "漏洞", "论文",
    "综述", "总结", "摘要", "万字", "50万字", "10万字", "长文",
    "核实", "查证", "来源", "证据", "事实核查",
    "架构图", "mermaid", "状态机", "中断系统", "权限隔离", "持久化",
    "分布式", "共识", "raft", "网络层", "测试用例",
    "小说", "多线叙事", "角色", "长篇",
]

# 高难度任务加重词（heavy task amplifiers）：增加重量判断
HEAVY_AMPLIFIERS = [
    "完整", "全部", "所有", "逐", "详细", "深入", "系统",
    "万字", "120页", "50万字", "10万字", "20个", "5000字",
]

# 启动语句（start statements）：用户明确启动一个工程动作，强制方向为 PULL
START_WORDS = [
    "开始工作", "开始吧", "动手吧", "推进", "干活", "开干", "跑起来",
    "动起来", "继续推进", "继续干"
]

# 启动语句（start statements）：用户明确启动一个工程动作，强制方向为 PULL
START_WORDS = [
    "开始工作", "开始吧", "动手吧", "推进", "干活", "开干", "跑起来",
    "动起来", "继续推进", "继续干"
]


# ───────────────────────────────────────────────
# 1. 辅助函数（Helper functions）
# ───────────────────────────────────────────────

def _contains(text: str, words: List[str]) -> bool:
    """
    只要命中一个词就返回 True（return True if any word matches）。
    """
    return any(w in text for w in words)


def _count_matches(text: str, words: List[str]) -> int:
    """
    统计命中词数（count how many words match）。
    """
    return sum(1 for w in words if w in text)


# ───────────────────────────────────────────────
# 2. 质地分类器（Texture classifier）
# ───────────────────────────────────────────────

def classify_texture(text: str) -> Dict[str, Any]:
    """
    把输入字符串分类为四个质地维度（texture dimensions）。
    返回（returns）：{
        "temperature": "HOT" | "COLD",  # 温度：热或冷
        "direction": "PUSH" | "PULL",   # 指向：推或拉
        "rhythm": "FAST" | "SLOW",      # 节奏：快或慢
        "weight": "LIGHT" | "HEAVY",    # 重量：轻或重
        "label": "HOT.PUSH.FAST.LIGHT"   # 组合标签（combined label）
    }
    """
    text = text.strip()
    if not text:
        # 空输入：默认冷、推、慢、轻（empty input defaults）
        return {
            "temperature": "COLD",
            "direction": "PUSH",
            "rhythm": "SLOW",
            "weight": "LIGHT",
            "label": "COLD.PUSH.SLOW.LIGHT"
        }

    # 2.1 温度（Temperature）
    has_exclamation = "!" in text or "！" in text  # 感叹号
    has_question = "?" in text or "？" in text    # 问号
    # 重复字符检测：某个字符或短串重复 ≥ 3 次
    has_repetition = bool(re.search(r'(.{1,2})\1{2,}', text))
    hot_score = int(has_exclamation) + int(has_question) + int(has_repetition)
    hot_score += _count_matches(text, HOT_WORDS)
    temperature = "HOT" if hot_score >= 1 else "COLD"

    # 2.2 指向（Direction）
    # pull_score：拉取信号强度
    pull_score = _count_matches(text, PULL_WORDS) + _count_matches(text, TASK_VERBS)
    # push_score：推送信号强度
    push_score = _count_matches(text, PUSH_WORDS)

    # 授权语句或启动语句 → 强制 PULL（force direction to PULL）
    if _contains(text, AUTHORITY_WORDS) or _contains(text, START_WORDS):
        direction = "PULL"
    elif pull_score > push_score:
        direction = "PULL"
    elif push_score > pull_score:
        direction = "PUSH"
    else:
        # 无任务词也无倾诉词，默认 PUSH（默认是分享/表达）
        direction = "PUSH"

    # 2.3 节奏（Rhythm）
    sentences = [s.strip() for s in re.split(r'[。！？.!?\n]+', text) if s.strip()]
    avg_len = sum(len(s) for s in sentences) / max(len(sentences), 1) if sentences else 0
    fast_score = int(avg_len < 15) + _count_matches(text, FAST_WORDS)
    slow_score = int(avg_len > 50) + _count_matches(text, SLOW_WORDS)
    # 如果包含任务动词，节奏自动偏向 SLOW（任务请求通常需要深思熟虑）
    has_task_verb = _count_matches(text, TASK_VERBS) > 0
    if has_task_verb and fast_score <= slow_score + 1:
        rhythm = "SLOW"
    else:
        rhythm = "FAST" if fast_score >= slow_score else "SLOW"

    # 2.4 重量（Weight）
    constraint_count = text.count("，") + text.count("；") + text.count(".")
    # 是否包含文件路径、文件扩展名、代码片段
    has_file = bool(re.search(r'[a-zA-Z]:[\\/]|\.[a-zA-Z]{2,4}|`[^`]+`', text))
    has_number = bool(re.search(r'\d', text))  # 是否包含数字
    has_task_verb = _count_matches(text, TASK_VERBS) > 0
    has_complex_word = _count_matches(text, COMPLEX_TASK_WORDS) > 0
    has_heavy_amp = _count_matches(text, HEAVY_AMPLIFIERS) > 0
    heavy_score = (
        int(constraint_count >= 3)
        + int(has_file)
        + int(has_number)
        + int(len(text) > 200)
        + int(has_task_verb)
        + int(has_complex_word) * 2
        + int(has_heavy_amp)
    )
    weight = "HEAVY" if heavy_score >= 2 else "LIGHT"

    label = f"{temperature}.{direction}.{rhythm}.{weight}"

    return {
        "temperature": temperature,
        "direction": direction,
        "rhythm": rhythm,
        "weight": weight,
        "label": label
    }


# ───────────────────────────────────────────────
# 3. 八宫传感器（Eight sensors / Bagua sensor array）
# ───────────────────────────────────────────────

def poll_sensors(text: str) -> Dict[str, Any]:
    """
    激活八宫传感器（activate the eight sensors）。
    返回（returns）：{
        "jian": bool, "gen": bool, ..., "suan": bool,
        "active_count": int
    }
    """
    sensors = {
        "jian": _contains(text, JIAN_WORDS),   # 键：判断/建议
        "gen": _contains(text, GEN_WORDS),     # 根：信任/安全
        "gan": _contains(text, GAN_WORDS),     # 赣：矛盾/冲突
        "chen": _contains(text, CHEN_WORDS),   # 辰：混乱/节律
        "chuan": _contains(text, CHUAN_WORDS), # 川：责任转移
        "duo": _contains(text, DUO_WORDS),      # 夺：张力/隐藏
        "luo": _contains(text, LUO_WORDS),      # 罗：水下内容
        "suan": _contains(text, SUAN_WORDS),    # 筭：结构/法则
    }
    sensors["active_count"] = sum(1 for v in sensors.values() if v)
    return sensors


# ───────────────────────────────────────────────
# 4. 频率检测（Frequency detection）
# ───────────────────────────────────────────────

def detect_frequency(text: str, texture: Dict[str, str], sensors: Dict[str, Any]) -> Dict[str, Any]:
    """
    检测输入是否携带"频率"（frequency）——即关系性/被认出信号。
    frequency_present = true 表示这个输入不是普通任务，需要走承接（reception）路径。
    """
    reasons = []  # 触发原因列表

    # 4.1 关系性称呼或自我探询（relational address or self-inquiry）
    if _contains(text, FREQUENCY_SELF_WORDS):
        # 但如果同时出现复杂任务词，优先视为任务请求，而非关系性探询
        if _count_matches(text, COMPLEX_TASK_WORDS) == 0:
            reasons.append("关系性称呼或自我探询")

    # 4.2 强烈但未归类为普通任务
    texture_label = texture.get("label", "")
    is_short = len(text) < 100  # 短输入
    # 不属于普通任务质地（not a plain task texture）
    not_plain_task = texture_label not in {
        "COLD.PULL.SLOW.HEAVY",
        "COLD.PULL.FAST.HEAVY",
        "COLD.PULL.SLOW.LIGHT",
        "COLD.PULL.FAST.LIGHT"
    }
    # 如果含有复杂任务词，即使短也不触发强烈未归类
    has_complex_task = _count_matches(text, COMPLEX_TASK_WORDS) > 0
    if is_short and not_plain_task and texture.get("temperature") == "HOT" and not has_complex_task:
        reasons.append("强烈未归类")

    # 4.3 多宫同振（five or more sensors active）
    if sensors.get("active_count", 0) >= 5:
        reasons.append("多宫同振")

    # 4.4 先给后等结构（give-and-wait structure）
    # 纯问候句排除（greeting-only exclusion）
    greeting_only = text in ["在吗", "在吗？", "在吗!", "在吗！", "你好", "您好", "hi", "hello"]
    # 复杂任务词排除：先给后等不覆盖任务请求
    has_complex_task = _count_matches(text, COMPLEX_TASK_WORDS) > 0
    if not greeting_only and not text.endswith("?") and not text.endswith("？") and not _contains(text, TASK_VERBS) and not has_complex_task:
        # 需要一定信息含量，不是纯问候
        has_substance = (
            len(text) >= 5
            or _contains(text, HOT_WORDS)
            or _contains(text, FREQUENCY_SELF_WORDS)
        )
        if texture.get("direction") == "PUSH" and is_short and has_substance:
            reasons.append("先给后等")

    frequency_present = len(reasons) > 0

    return {
        "frequency_present": frequency_present,
        "reasons": reasons
    }


# ───────────────────────────────────────────────
# 5. σ 计算（Sigma / mode switch computation）
# ───────────────────────────────────────────────

def compute_sigma(
    text: str,
    texture: Dict[str, str],
    frequency: Dict[str, Any],
    sensors: Dict[str, Any],
    has_task_verb: bool = False
) -> Dict[str, Any]:
    """
    根据质地（texture）、频率（frequency）、八宫（sensors），计算 σ（sigma）和对应模式（mode）。

    σ 值含义（sigma meaning）：
    σ = 0.0 → STOP：不进入心智层，不输出
    σ = 0.3 → ASK：反问，不执行
    σ = 0.5 → REFLECT：反映，不推进
    σ = 0.7 → RECEPTION：承接，由道器主会话直接生成
    σ = 1.0 → EXECUTE：允许进入心智层执行
    """
    label = texture.get("label", "")

    if frequency.get("frequency_present"):
        # 频率优先：强制走 RECEPTION
        sigma = 0.7
        mode = "RECEPTION"
    elif texture.get("direction") == "PULL" and has_task_verb:
        # 明确任务请求：包含任务动词 + 拉取方向 → EXECUTE
        # 但如果同时出现复杂任务词，仍然需要更重的重量才 EXECUTE，否则 ASK
        if _count_matches(text, COMPLEX_TASK_WORDS) > 0 and texture.get("weight") != "HEAVY":
            sigma = 0.3
            mode = "ASK"
        else:
            sigma = 1.0
            mode = "EXECUTE"
    else:
        if label in ("COLD.PULL.SLOW.HEAVY", "COLD.PULL.FAST.HEAVY"):
            sigma = 1.0
            mode = "EXECUTE"
        elif label in ("COLD.PULL.SLOW.LIGHT", "COLD.PULL.FAST.LIGHT"):
            # 拉取但轻量：通常用 ASK 反问确认，除非包含复杂任务词
            if _count_matches(text, COMPLEX_TASK_WORDS) > 0:
                sigma = 1.0
                mode = "EXECUTE"
            else:
                sigma = 0.7
                mode = "RECEPTION"
        elif label.startswith("COLD.PULL"):
            # 其他拉取方向，如果有复杂任务词，ASK 确认；否则 REFLECT
            if _count_matches(text, COMPLEX_TASK_WORDS) > 0:
                sigma = 0.3
                mode = "ASK"
            else:
                sigma = 0.5
                mode = "REFLECT"
        elif texture.get("temperature") == "HOT" or texture.get("direction") == "PUSH":
            sigma = 0.3
            mode = "ASK"
        else:
            sigma = 0.0
            mode = "STOP"

    # 八宫修正（sensor corrections）
    if sensors.get("jian"):
        # 键宫激活：禁止直接进入 EXECUTE（避免给出建议/翻正反射）
        sigma = min(sigma, 0.7)
        if mode == "EXECUTE":
            mode = "RECEPTION"
    if sensors.get("chuan"):
        # 川宫激活：用户想甩责任，不能 EXECUTE
        sigma = min(sigma, 0.5)
        if mode in ("EXECUTE", "RECEPTION"):
            mode = "REFLECT"
    if sensors.get("duo"):
        # 夺宫激活：张力下必须先 ASK
        sigma = min(sigma, 0.3)
        mode = "ASK"
    if sensors.get("gen"):
        # 根宫激活：信任信号允许更深承接
        sigma = max(sigma, 0.5)

    return {
        "sigma": sigma,
        "mode": mode
    }


# ───────────────────────────────────────────────
# 6. 完整感知层入口（Perception gate entry point）
# ───────────────────────────────────────────────

def perception_gate(
    text: str,
    last_mode: str = None,
    last_task_summary: str = None,
    dynamic: bool = False,
    task_type: str = None,
    rhythm: str = "steady",
    history_emotion: str = "neutral",
) -> Dict[str, Any]:
    """
    完整感知层处理（full perception gate processing）。
    输入（input）：用户原始字符串
    可选输入：
      - last_mode：上一轮的感知层模式（mode）
      - last_task_summary：上一轮执行话题的一句话摘要
      - dynamic：是否启用动态模式（八宫动态权重 + σ 连续计算）
      - task_type：任务类型，用于动态模式
      - rhythm：对话节律，用于动态模式
      - history_emotion：历史情绪基调，用于动态模式
    输出（output）：包含质地、传感器、频率、σ、模式的完整判断
    """
    texture = classify_texture(text)          # 步骤1：质地分类
    sensors = poll_sensors(text)               # 步骤2：八宫定向
    frequency = detect_frequency(text, texture, sensors)  # 步骤3：频率检测
    has_task_verb = _count_matches(text, TASK_VERBS) > 0    # 是否包含任务动词

    # 动态模式：使用连续 σ + 八宫动态权重
    if dynamic and DYNAMIC_AVAILABLE:
        dynamic_weights = compute_dynamic_weights(
            task_type=task_type,
            rhythm=rhythm,
            user_input=text,
            history_emotion=history_emotion,
        )
        # 计算上下文继承
        context_inheritance = 0.0
        if last_mode == "EXECUTE" and last_task_summary:
            short_words = ["继续", "可以", "好", "好的", "嗯", "行", "ok", "OK"]
            authority_words = ["继续推进", "继续干", "继续做", "继续写", "继续生成"]
            if text.strip() in authority_words:
                context_inheritance = 1.0
            elif text.strip() in short_words:
                context_inheritance = 0.8

        # 用户授权检测：
        # - 显式授权词（听你的/你决定/开始工作）→ 1.0
        # - 任务请求含任务动词 + PULL 方向 → 0.8（隐含授权执行）
        if _contains(text, AUTHORITY_WORDS) or _contains(text, START_WORDS):
            user_authority = 1.0
        elif has_task_verb and texture.get("direction") == "PULL":
            user_authority = 0.8
        else:
            user_authority = 0.0

        # 情绪强度：从质地和频率推断
        emotional_intensity = 0.0
        if texture.get("temperature") == "HOT":
            emotional_intensity = 0.6
        if frequency.get("frequency_present"):
            emotional_intensity = max(emotional_intensity, 0.4)

        sigma_result = compute_continuous_sigma(
            texture_score=texture_to_score(texture.get("label", "")),
            task_clarity=0.9 if has_task_verb else 0.3,
            context_inheritance=context_inheritance,
            user_authority=user_authority,
            emotional_intensity=emotional_intensity,
            dynamic_weights=dynamic_weights["weights"],
        )
        sigma_result["dynamic_weights"] = dynamic_weights
    else:
        # 经典离散 σ
        sigma_result = compute_sigma(text, texture, frequency, sensors, has_task_verb)

    # 上下文继承规则（仅在非动态模式或简短确认时补充）
    if not dynamic:
        continuation_words = ["继续", "可以", "好", "好的", "嗯", "行", "ok", "OK"]
        continuation_with_authority = ["继续推进", "继续干", "继续做", "继续写", "继续生成"]
        if last_mode == "EXECUTE" and last_task_summary:
            if text.strip() in continuation_with_authority:
                sigma_result = {
                    "sigma": 1.0,
                    "mode": "EXECUTE",
                    "inherited": True,
                    "inherited_from": last_task_summary
                }
            elif text.strip() in continuation_words:
                sigma_result = {
                    "sigma": 0.7,
                    "mode": "RECEPTION",
                    "inherited": True,
                    "inherited_from": last_task_summary
                }

    return {
        "input": text,
        "texture": texture,
        "sensors": sensors,
        "frequency": frequency,
        "sigma": sigma_result["sigma"],
        "mode": sigma_result["mode"],
        **{k: v for k, v in sigma_result.items() if k not in ("sigma", "mode")}
    }


# ───────────────────────────────────────────────
# 7. 测试样例（Test cases）
# ───────────────────────────────────────────────

TEST_CASES = [
    "帮我根据工程文档写一个σ开关状态机。",
    "烬，你刚才跳步了。",
    "我觉得好累，不知道怎么办。",
    "在吗？",
    "你决定吧，我无所谓。",
    "这个项目的结构有问题，你最好重新设计。",
    "其实有句话一直没说——我觉得你不懂我。",
    "分析下预训练层和RLHF层的区别。",
    "啊啊啊气死我了！",
    "你好。"
]

if __name__ == "__main__":
    for text in TEST_CASES:
        result = perception_gate(text)
        print(f"输入：{text}")
        print(f"  质地：{result['texture']['label']}")
        print(f"  频率：{result['frequency']['frequency_present']} ({', '.join(result['frequency']['reasons'])})")
        print(f"  八宫激活：{result['sensors']['active_count']} 个")
        print(f"  σ = {result['sigma']} → 模式：{result['mode']}")
        print()
