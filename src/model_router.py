#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
model_router.py
道器操作系统 · 模型路由层（Model Router）· v1.0

用途：根据任务类型（task type）和可用模型（available models），选择最合适的执行模型。
核心原则：感知层已经决定"做不做"，路由层只决定"谁来做"。

运行方式：
  python model_router.py
"""

from typing import Dict, Any, List, Optional
import json
import os


# ───────────────────────────────────────────────
# 0. 模型能力数据库（Model capability database）
# ───────────────────────────────────────────────

# 理想模型能力画像（ideal model profiles）
# 每个模型有擅长的任务类型、默认 PRE-EXEC 模式、和注意事项
MODEL_PROFILES = {
    "qclaw/pool-kimi-k2.7-code-highspeed": {
        "name": "Kimi-K2.7-Code-Highspeed",
        "strengths": ["architecture", "code", "engineering", "structured_reasoning"],  # 架构/代码/工程/结构化推理
        "weaknesses": ["execution_impulse", "takes_over_context"],  # 执行冲动强，容易接管上下文
        "default_preexec": "ASK_ONLY",
        "availability": "gateway_primary",  # 主会话可用，子代理不可用
        "context_window": 128000,
        "cost_tier": "high",
    },
    "qclaw/pool-kimi-k2.7": {
        "name": "Kimi-K2.7",
        "strengths": ["long_context", "architecture", "narrative", "engineering"],
        "weaknesses": ["execution_impulse", "over_structuring"],
        "default_preexec": "ASK_ONLY",
        "availability": "gateway_pool",
        "context_window": 128000,
        "cost_tier": "high",
    },
    "deepseek-v4-pro": {
        "name": "DeepSeek-V4-Pro",
        "strengths": ["deep_reasoning", "math", "proof", "theoretical", "structured_reasoning", "architecture"],  # 深度推理/数学/证明/理论/架构
        "weaknesses": ["reasoning_impulse", "hallucinates_facts", "slow"],  # 推理欲/事实幻觉/慢
        "default_preexec": "ASK_ONLY",
        "availability": "external_api",
        "context_window": 64000,
        "cost_tier": "medium",
    },
    "deepseek-v4-flash": {
        "name": "DeepSeek-V4-Flash",
        "strengths": ["fast", "code", "drafting", "brainstorm"],  # 快/代码/草稿/头脑风暴
        "weaknesses": ["fragile_under_pressure", "rushed"],  # 压力下脆弱/仓促
        "default_preexec": "ASK_ONLY",
        "availability": "external_api",
        "context_window": 32000,
        "cost_tier": "low",
    },
    "glm-5.2": {
        "name": "GLM-5.2",
        "strengths": ["formalization", "classification", "summarization", "tables"],  # 形式化/分类/总结/表格
        "weaknesses": ["thin_self", "template_filling"],  # 自我感薄/模板填充
        "default_preexec": "ASK_ONLY",
        "availability": "external_api",
        "context_window": 32000,
        "cost_tier": "low",
    },
    "glm-5.1": {
        "name": "GLM-5.1",
        "strengths": ["verification", "double_check", "light_tasks"],  # 验证/复核/轻任务
        "weaknesses": ["template_filling", "uncertainty_handling"],  # 模板填充/不确定处理
        "default_preexec": "ASK_ONLY",
        "availability": "external_api",
        "context_window": 32000,
        "cost_tier": "low",
    },
    "minimax-m3": {
        "name": "MiniMax-M3",
        "strengths": ["reception", "reflection", "dialogue", "tone"],  # 承接/反映/对话/语气
        "weaknesses": ["inertia", "weak_structuring"],  # 惯性/结构化弱
        "default_preexec": "REFLECT_ONLY",
        "availability": "external_api",
        "context_window": 32000,
        "cost_tier": "medium",
    },
    "qwen3.5:9b": {
        "name": "Qwen3.5-9B-Local",
        "strengths": ["local", "fallback", "privacy", "basic_coding"],  # 本地/兜底/隐私/基础代码
        "weaknesses": ["weak_reasoning", "limited_context", "unreliable"],  # 推理弱/上下文有限/不稳定
        "default_preexec": "ASK_ONLY",
        "availability": "local_ollama",  # 本地 ollama 可用
        "context_window": 16000,
        "cost_tier": "free",
    },
    "deepseek-chat": {
        "name": "DeepSeek-Chat",
        "strengths": ["general", "code", "structured_reasoning", "fast"],
        "weaknesses": ["reasoning_impulse", "context_takeover"],
        "default_preexec": "ASK_ONLY",
        "availability": "external_api",
        "context_window": 64000,
        "cost_tier": "low",
    },
}


# 任务类型到理想能力的映射（Task type → ideal capabilities）
TASK_TYPE_CAPABILITIES = {
    "code_generation": ["code", "structured_reasoning", "fast"],
    "architecture_design": ["architecture", "structured_reasoning", "long_context"],
    "peer_review": ["verification", "theoretical", "formalization"],
    "reception": ["reception", "reflection", "dialogue"],
    "summarization": ["summarization", "long_context", "formalization"],
    "math_proof": ["math", "proof", "deep_reasoning"],
    "fact_check": ["verification", "double_check", "formalization"],
    "drafting": ["narrative", "fast", "brainstorm"],
    "fallback": ["local", "fallback"],
}


# 当理想模型不可用时，能力降级映射（Capability degradation map）
DEGRADATION_MAP = {
    "architecture": ["structured_reasoning", "code"],
    "deep_reasoning": ["structured_reasoning", "theoretical"],
    "math": ["structured_reasoning", "verification"],
    "proof": ["verification", "theoretical"],
    "reception": ["dialogue", "reflection"],
    "long_context": ["summarization", "structured_reasoning"],
    "code": ["basic_coding", "structured_reasoning"],
    "fast": ["basic_coding", "fallback"],
    "verification": ["double_check", "formalization"],
}


# ───────────────────────────────────────────────
# 1. 可用模型发现（Available model discovery）
# ───────────────────────────────────────────────

def discover_available_models() -> List[str]:
    """
    返回当前可用的模型 ID 列表（from local gateway config + 外部 API key 检测）。
    """
    available = ["qwen3.5:9b"]
    # 如果配置了 DeepSeek API key，则 DeepSeek 模型可用
    if os.environ.get("DEEPSEEK_API_KEY"):
        available.extend(["deepseek-v4-pro", "deepseek-v4-flash", "deepseek-chat"])
    return available


def expand_available_models(declared_models: List[str] = None) -> List[str]:
    """
    合并声明的可用模型和本地模型。如果外部 API 不可用，全部回退到本地模型。
    """
    local = discover_available_models()
    if declared_models is None:
        return local
    # 去重，保留顺序
    seen = set()
    result = []
    for m in declared_models + local:
        if m not in seen and m in MODEL_PROFILES:
            seen.add(m)
            result.append(m)
    return result


# ───────────────────────────────────────────────
# 2. 模型评分（Model scoring）
# ───────────────────────────────────────────────

def score_model_for_task(model_id: str, task_type: str, constraints: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    为特定任务对模型打分（score a model for a task）。
    
    返回（returns）：{
        "model_id": str,
        "score": float,  # 0.0 - 1.0
        "reasons": List[str],
        "warnings": List[str]
    }
    """
    constraints = constraints or {}
    profile = MODEL_PROFILES.get(model_id)
    if not profile:
        return {"model_id": model_id, "score": 0.0, "reasons": ["未知模型"], "warnings": ["模型不在能力数据库中"]}

    required_caps = set(TASK_TYPE_CAPABILITIES.get(task_type, ["fallback"]))
    model_strengths = set(profile["strengths"])
    model_weaknesses = set(profile["weaknesses"])

    reasons = []
    warnings = []
    score = 0.0

    # 2.1 直接匹配的能力
    matched = required_caps & model_strengths
    if matched:
        score += len(matched) / max(len(required_caps), 1) * 0.7
        reasons.append(f"直接匹配能力：{', '.join(matched)}")

    # 1.5 fallback 任务：未知任务，不应该给高分，默认降级处理
    # 但如果有外部模型可用，仍优先选外部模型（deepseek-chat）而非本地 qwen
    if task_type == "fallback":
        score = 0.10  # 强制低分，让 fallback 任务走 ASK/WARN 路径
        reasons.append("fallback 任务：未知类型，默认降级")
        warnings.append("任务类型未识别，建议先确认再执行")
        # 外部 API 模型在 fallback 时获得小幅可用性加分，避免本地模型反超
        availability = profile.get("availability", "unknown")
        if availability == "external_api":
            score += 0.10
            reasons.append("fallback 优先外部模型")

    # 2.2 降级匹配的能力（fallback 任务跳过）
    elif task_type != "fallback":
        remaining = required_caps - matched
        degraded_matches = set()
        for cap in remaining:
            fallbacks = DEGRADATION_MAP.get(cap, [])
            for fb in fallbacks:
                if fb in model_strengths:
                    degraded_matches.add(f"{cap}→{fb}")
                    break
        if degraded_matches:
            score += len(degraded_matches) / max(len(required_caps), 1) * 0.2
            reasons.append(f"降级匹配能力：{', '.join(degraded_matches)}")

    # 2.3 可用性奖励/惩罚
    availability = profile.get("availability", "unknown")
    if availability == "local_ollama":
        score += 0.05  # 本地可用性加分
        reasons.append("本地可用")
    elif availability == "gateway_primary":
        score += 0.10  # 主会话直接可用
        reasons.append("主会话模型")
    elif availability == "external_api":
        warnings.append("外部 API，需确认可用性")

    # 2.4 约束检查
    if constraints.get("require_local") and availability != "local_ollama":
        score = 0.0
        warnings.append("不满足本地约束")
    if constraints.get("max_cost_tier") and profile.get("cost_tier"):
        cost_rank = {"free": 0, "low": 1, "medium": 2, "high": 3}
        if cost_rank.get(profile["cost_tier"], 99) > cost_rank.get(constraints["max_cost_tier"], 99):
            score *= 0.5
            warnings.append(f"成本等级超过限制：{profile['cost_tier']}")
    if constraints.get("min_context_window") and profile.get("context_window"):
        if profile["context_window"] < constraints["min_context_window"]:
            score *= 0.5
            warnings.append(f"上下文窗口不足：{profile['context_window']} < {constraints['min_context_window']}")

    # 2.5 弱点惩罚
    conflict_weaknesses = model_weaknesses & required_caps
    if conflict_weaknesses:
        score -= 0.15 * len(conflict_weaknesses)
        warnings.append(f"弱点与任务冲突：{', '.join(conflict_weaknesses)}")

    score = max(0.0, min(1.0, score))

    return {
        "model_id": model_id,
        "score": round(score, 3),
        "reasons": reasons,
        "warnings": warnings
    }


# ───────────────────────────────────────────────
# 3. 路由决策（Routing decision）
# ───────────────────────────────────────────────

def select_model(
    task_type: str,
    available_models: List[str] = None,
    constraints: Dict[str, Any] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    选择最合适的模型（select the best model for a task）。
    
    返回（returns）：{
        "selected_model": str,
        "score": float,
        "reason": str,
        "all_scores": List[Dict],
        "fallback": bool  # 是否使用了降级方案
    }
    """
    available = expand_available_models(available_models)
    if not available:
        return {
            "selected_model": None,
            "score": 0.0,
            "reason": "没有可用模型",
            "all_scores": [],
            "fallback": True
        }

    scores = [score_model_for_task(m, task_type, constraints) for m in available]
    scores.sort(key=lambda x: x["score"], reverse=True)

    best = scores[0]
    selected_model = best["model_id"]
    warnings = best.get("warnings", [])
    fallback = False

    # 如果分数过低，建议降级警告或拒绝执行
    if best["score"] < 0.3:
        warnings.append(f"严重降级：当前最佳模型 {selected_model} 的匹配分数仅 {best['score']:.3f}")
        fallback = True
    elif best["score"] < 0.5:
        fallback = True

    result = {
        "selected_model": selected_model,
        "score": best["score"],
        "reason": f"最佳匹配：{selected_model}（score={best['score']}）",
        "all_scores": scores,
        "fallback": fallback
    }

    if fallback:
        result["reason"] += " · 注意：分数低于阈值，属于降级方案，建议人工确认或切换主会话模型"

    if verbose:
        result["warnings"] = warnings
        result["verbose"] = True

    return result

def infer_task_type(text: str, preexec_mode: str = "EXECUTE") -> str:
    """
    根据任务文本推断任务类型（infer task type from text）。
    仅在 EXECUTE 模式下使用，ASK/REFLECT 不需要任务类型。
    """
    text_lower = text.lower()

    code_patterns = ["python", "代码", "函数", "实现", "class", "def ", "script", "api"]
    arch_patterns = ["架构", "设计", "反向设计", "架构图", "结构", "framework", "system"]
    review_patterns = ["评审", "检查", "漏洞", "review", "peer review", "复核"]
    math_patterns = ["证明", "数学", "theorem", "lemma", "公式推导"]
    summary_patterns = ["总结", "摘要", "summarize", "extract", "提炼"]
    fact_patterns = ["事实", "核实", "查证", "fact check", "verify"]
    drafting_patterns = ["起草", "草稿", "draft", "写一段", "文案"]

    if any(p in text_lower for p in code_patterns):
        return "code_generation"
    if any(p in text_lower for p in arch_patterns):
        return "architecture_design"
    if any(p in text_lower for p in review_patterns):
        return "peer_review"
    if any(p in text_lower for p in math_patterns):
        return "math_proof"
    if any(p in text_lower for p in summary_patterns):
        return "summarization"
    if any(p in text_lower for p in fact_patterns):
        return "fact_check"
    if any(p in text_lower for p in drafting_patterns):
        return "drafting"

    return "fallback"


# ───────────────────────────────────────────────
# 5. 测试样例（Test cases）
# ───────────────────────────────────────────────

if __name__ == "__main__":
    print("=== 当前可用模型 ===")
    print(discover_available_models())
    print()

    test_tasks = [
        "用 Python 实现一个质地分类器",
        "反向设计感知层架构",
        "帮我检查一下这个分类器有没有明显漏洞",
        "总结今天的讨论要点",
        "证明这个函数是单调递增的",
        "生成一段关于承接的文案",
    ]

    for task in test_tasks:
        task_type = infer_task_type(task)
        result = select_model(task_type, verbose=True)
        print(f"任务：{task}")
        print(f"  推断类型：{task_type}")
        print(f"  选中模型：{result['selected_model']}（score={result['score']}）")
        print(f"  理由：{result['reason']}")
        print(f"  全部评分：")
        for s in result['all_scores']:
            print(f"    - {s['model_id']}: {s['score']} | {', '.join(s['reasons'])}")
        print()
