#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
error_recovery.py
道器操作系统 · 错误恢复与降级模块 · v0.1

用途：当外部模型调用失败或超时时，自动降级到备用方案。
"""

import os
from typing import Dict, Any, Optional, Callable
from deepseek_client import call_deepseek


def call_with_recovery(
    model_id: str,
    task: str,
    system_prompt: str = "",
    fallback_chain: list = None,
    max_retries: int = 1,
    timeout: int = 60
) -> Dict[str, Any]:
    """
    带错误恢复的外部模型调用。

    参数：
      model_id: 首选模型
      task: 任务文本
      system_prompt: 系统提示
      fallback_chain: 降级链，如 ["deepseek-v4-pro", "deepseek-chat", "qwen3.5:9b"]
      max_retries: 对首选模型重试次数
      timeout: 超时秒数

    返回：{
        "success": bool,
        "model_used": str,
        "output": str,
        "error": str or None,
        "fallback_used": bool
    }
    """
    fallback_chain = fallback_chain or []
    all_models = [model_id] + [m for m in fallback_chain if m != model_id]

    for attempt, m in enumerate(all_models):
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": task})

            result = call_deepseek(model=m, messages=messages, timeout=timeout)
            content = result["choices"][0]["message"]["content"]
            return {
                "success": True,
                "model_used": m,
                "output": content,
                "error": None,
                "fallback_used": attempt > 0,
            }
        except Exception as e:
            last_error = str(e)
            # 如果是最后一个模型，返回失败
            if attempt == len(all_models) - 1:
                return {
                    "success": False,
                    "model_used": m,
                    "output": "",
                    "error": last_error,
                    "fallback_used": attempt > 0,
                }
            # 否则继续降级
            continue


def fallback_to_local(task: str, mode: str = "ASK_ONLY") -> Dict[str, Any]:
    """本地兜底响应。"""
    if mode == "ASK_ONLY":
        output = (
            "外部模型暂时不可用。在继续之前，我想确认：\n"
            "1. 你当前最想推进的方向是什么？\n"
            "2. 是否有预算或网络限制需要考虑？"
        )
    elif mode == "REFLECT_ONLY":
        output = "外部模型暂时不可用。我此刻只是在这里，不急着推进。"
    elif mode == "EXECUTE":
        output = "外部模型暂时不可用，执行请求已暂停。建议先确认任务细节，或稍后再试。"
    else:
        output = "外部模型暂时不可用。"

    return {
        "success": True,
        "model_used": "qwen3.5:9b-local-fallback",
        "output": output,
        "error": None,
        "fallback_used": True,
    }


if __name__ == "__main__":
    # 测试：使用一个无效模型触发降级链
    result = call_with_recovery(
        model_id="deepseek-invalid-model",
        task="测试错误恢复",
        system_prompt="你是一个测试助手。",
        fallback_chain=["deepseek-chat", "deepseek-v4-pro"],
    )
    print(result)
