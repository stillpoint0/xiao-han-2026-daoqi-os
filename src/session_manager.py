#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
session_manager.py
道器操作系统 · 多轮对话管理器 · v0.1

用途：统一管理多轮对话状态，包括上下文继承、主题漂移检测、对话节律感知。
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

DEFAULT_SESSION_DB = "session_db.jsonl"


class SessionManager:
    """
    多轮对话管理器。

    核心职责：
      1. 维护当前轮次的上下文
      2. 提供上下文继承建议
      3. 检测主题漂移
      4. 感知对话节律（轮次间隔、情绪变化）
    """

    def __init__(self, db_path: str = DEFAULT_SESSION_DB):
        self.db_path = Path(db_path)
        self.turns: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        """加载历史轮次。"""
        if self.db_path.exists():
            with open(self.db_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            self.turns.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue

    def add_turn(
        self,
        user_input: str,
        mode: str,
        task_summary: str = None,
        selected_model: str = None,
        cost: float = 0.0,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """记录一轮对话。"""
        now = datetime.now().isoformat()
        turn = {
            "turn_id": len(self.turns) + 1,
            "timestamp": now,
            "user_input": user_input,
            "mode": mode,
            "task_summary": task_summary,
            "selected_model": selected_model,
            "cost": cost,
            "metadata": metadata or {},
        }
        self.turns.append(turn)
        with open(self.db_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(turn, ensure_ascii=False) + "\n")
        return turn

    def get_last_turn(self) -> Optional[Dict[str, Any]]:
        """获取上一轮。"""
        if not self.turns:
            return None
        return self.turns[-1]

    def get_context_summary(self, n: int = 3) -> Dict[str, Any]:
        """
        获取最近 n 轮的核心上下文摘要。
        返回 last_mode、last_task_summary、recent_tasks、rhythm。
        """
        recent = self.turns[-n:] if len(self.turns) >= n else self.turns
        if not recent:
            return {
                "last_mode": None,
                "last_task_summary": None,
                "recent_tasks": [],
                "rhythm": "empty",
            }

        last = recent[-1]
        recent_tasks = [t.get("task_summary") for t in recent if t.get("task_summary")]

        # 节律感知
        rhythm = self._detect_rhythm(recent)

        return {
            "last_mode": last.get("mode"),
            "last_task_summary": last.get("task_summary"),
            "recent_tasks": recent_tasks,
            "rhythm": rhythm,
        }

    def _detect_rhythm(self, recent: List[Dict[str, Any]]) -> str:
        """
        感知对话节律。
        - fast：连续 EXECUTE
        - pause：从 EXECUTE 转到 ASK/REFLECT/RECEPTION
        - drift：任务主题变化
        - steady：保持同一主题
        """
        modes = [t.get("mode") for t in recent]
        tasks = [t.get("task_summary") for t in recent if t.get("task_summary")]

        # 连续执行
        if all(m == "EXECUTE" for m in modes):
            return "fast"

        # 停顿信号
        if len(modes) >= 2 and modes[-2] == "EXECUTE" and modes[-1] in ("ASK", "REFLECT", "RECEPTION"):
            return "pause"

        # 主题漂移
        if len(tasks) >= 2 and tasks[-1] != tasks[-2]:
            return "drift"

        return "steady"

    def should_inherit(self, user_input: str) -> Dict[str, Any]:
        """
        判断本轮是否应该继承上一轮上下文。
        返回：{"inherit": bool, "last_mode": str, "last_task_summary": str, "reason": str}
        """
        last = self.get_last_turn()
        if not last:
            return {"inherit": False, "last_mode": None, "last_task_summary": None, "reason": "无历史"}

        # 如果输入非常短，且上一轮是 EXECUTE，建议继承
        short_words = ["继续", "好", "好的", "嗯", "行", "ok", "OK"]
        if last.get("mode") == "EXECUTE" and user_input.strip() in short_words:
            return {
                "inherit": True,
                "last_mode": last.get("mode"),
                "last_task_summary": last.get("task_summary"),
                "reason": "简短确认词，继承上一轮 EXECUTE 上下文",
            }

        # 如果输入包含指代词，建议继承
        reference_words = ["这个", "那个", "它", "刚才", "上面", "之前"]
        if any(w in user_input for w in reference_words):
            return {
                "inherit": True,
                "last_mode": last.get("mode"),
                "last_task_summary": last.get("task_summary"),
                "reason": "含指代词，继承上下文",
            }

        return {
            "inherit": False,
            "last_mode": last.get("mode"),
            "last_task_summary": last.get("task_summary"),
            "reason": "输入足够独立，不继承",
        }

    def detect_topic_drift(self, user_input: str, threshold: int = 3) -> Dict[str, Any]:
        """
        简单主题漂移检测。
        如果输入包含新的动词或名词，且与最近任务关键词无重叠，认为可能漂移。
        """
        last_task = self.get_last_turn()
        last_task_summary = (last_task.get("task_summary") or "") if last_task else ""

        # 简单分词：取 2 字以上关键词
        def extract_keywords(text: str) -> set:
            words = set()
            for i in range(len(text) - 1):
                w = text[i:i+2]
                if any(ord(c) > 127 for c in w):
                    words.add(w)
            return words

        input_kw = extract_keywords(user_input)
        task_kw = extract_keywords(last_task_summary)

        overlap = input_kw & task_kw
        drift_score = len(input_kw - overlap) - len(overlap)

        return {
            "drift_score": drift_score,
            "is_drift": drift_score > threshold,
            "overlap": list(overlap),
            "new_topics": list(input_kw - overlap),
        }


if __name__ == "__main__":
    sm = SessionManager()

    # 模拟三轮对话
    sm.add_turn("帮我用 Python 实现一个质地分类器", "EXECUTE", "code_generation", "deepseek-chat", 0.015)
    sm.add_turn("继续", "EXECUTE", "code_generation", "deepseek-chat", 0.012)
    sm.add_turn("我觉得这个方向不对", "RECEPTION", None, None, 0.0)

    print("上下文摘要：", sm.get_context_summary())
    print("是否应该继承'继续推进'：", sm.should_inherit("继续推进"))
    print("是否应该继承'帮我写首诗'：", sm.should_inherit("帮我写首诗"))
    print("主题漂移检测'写首诗'：", sm.detect_topic_drift("帮我写首诗"))
