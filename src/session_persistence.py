#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
session_persistence.py
道器操作系统 · 会话持久化模块 · v0.1

用途：保存和恢复多轮对话的状态，包括 last_mode、last_task_summary、累计成本、历史任务。
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

DEFAULT_SESSION_PATH = "session_state.json"


class SessionState:
    """会话状态管理器。"""

    def __init__(self, session_path: str = DEFAULT_SESSION_PATH):
        self.session_path = Path(session_path)
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        """从文件加载状态。"""
        if self.session_path.exists():
            try:
                with open(self.session_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass
        return self._default_state()

    def _default_state(self) -> Dict[str, Any]:
        """默认状态。"""
        return {
            "version": "0.1",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "last_mode": None,
            "last_task_summary": None,
            "last_user_input": None,
            "last_selected_model": None,
            "history": [],
            "total_cost_cny": 0.0,
        }

    def save(self):
        """保存状态到文件。"""
        self.data["updated_at"] = datetime.now().isoformat()
        with open(self.session_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def update(
        self,
        last_mode: str = None,
        last_task_summary: str = None,
        last_user_input: str = None,
        last_selected_model: str = None,
        cost_delta: float = 0.0,
    ):
        """更新状态。"""
        if last_mode is not None:
            self.data["last_mode"] = last_mode
        if last_task_summary is not None:
            self.data["last_task_summary"] = last_task_summary
        if last_user_input is not None:
            self.data["last_user_input"] = last_user_input
        if last_selected_model is not None:
            self.data["last_selected_model"] = last_selected_model
        if cost_delta:
            self.data["total_cost_cny"] += cost_delta

        # 记录历史
        entry = {
            "timestamp": datetime.now().isoformat(),
            "mode": last_mode,
            "task_summary": last_task_summary,
            "user_input": last_user_input,
            "selected_model": last_selected_model,
            "cost_delta": cost_delta,
        }
        self.data["history"].append(entry)
        self.save()

    def get(self) -> Dict[str, Any]:
        """获取当前状态。"""
        return self.data

    def clear(self):
        """清空状态。"""
        self.data = self._default_state()
        self.save()


if __name__ == "__main__":
    state = SessionState()
    state.update(
        last_mode="EXECUTE",
        last_task_summary="实现质地分类器",
        last_user_input="帮我用 Python 实现一个质地分类器",
        last_selected_model="deepseek-chat",
        cost_delta=0.012,
    )
    print("当前状态：", json.dumps(state.get(), ensure_ascii=False, indent=2))
