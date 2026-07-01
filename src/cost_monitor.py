#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cost_monitor.py
道器操作系统 · 成本监控模块 · v0.1

用途：记录每次外部 API 调用的成本，提供预算告警和累计统计。
设计原则：成本监控不依赖外部模型，只记录本地元数据。
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


# 默认价格：每 1K token（人民币元）
# 实际价格以 DeepSeek 官方为准，这里使用估算值
DEFAULT_PRICING = {
    "deepseek-v4-pro": {"input": 0.004, "output": 0.016},
    "deepseek-v4-flash": {"input": 0.001, "output": 0.004},
    "deepseek-chat": {"input": 0.001, "output": 0.002},
    "glm-5.2": {"input": 0.001, "output": 0.002},
    "glm-5.1": {"input": 0.0005, "output": 0.001},
    "minimax-m3": {"input": 0.0015, "output": 0.006},
    "qwen3.5:9b": {"input": 0.0, "output": 0.0},
}

DEFAULT_BUDGET_CNY = 50.0  # 默认预算 50 元


class CostMonitor:
    """成本监控器。记录每次调用、累计成本、预算告警。"""

    def __init__(self, log_path: str = "cost_log.jsonl", budget: float = DEFAULT_BUDGET_CNY):
        self.log_path = Path(log_path)
        self.budget = budget
        self._records = []
        self._load_existing()

    def _load_existing(self):
        """加载已有记录。"""
        if self.log_path.exists():
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            self._records.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue

    def record(self, model_id: str, input_tokens: int, output_tokens: int, task: str = "") -> Dict[str, Any]:
        """记录一次 API 调用。"""
        pricing = DEFAULT_PRICING.get(model_id, {"input": 0.0, "output": 0.0})
        input_cost = (input_tokens / 1000.0) * pricing["input"]
        output_cost = (output_tokens / 1000.0) * pricing["output"]
        total_cost = input_cost + output_cost

        record = {
            "timestamp": datetime.now().isoformat(),
            "model_id": model_id,
            "task": task,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(total_cost, 6),
        }
        self._records.append(record)

        # 追加写入日志
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        return record

    def total_cost(self) -> float:
        """累计总成本。"""
        return sum(r["total_cost"] for r in self._records)

    def remaining_budget(self) -> float:
        """剩余预算。"""
        return self.budget - self.total_cost()

    def budget_status(self) -> Dict[str, Any]:
        """预算状态。"""
        total = self.total_cost()
        remaining = self.budget - total
        ratio = total / self.budget if self.budget > 0 else 0.0
        level = "safe"
        if ratio >= 0.9:
            level = "critical"
        elif ratio >= 0.7:
            level = "warning"
        elif ratio >= 0.5:
            level = "notice"

        return {
            "budget": self.budget,
            "total_cost": round(total, 6),
            "remaining": round(remaining, 6),
            "ratio": round(ratio, 4),
            "level": level,
            "records_count": len(self._records),
        }

    def check_budget(self, estimated_cost: float = 0.0) -> Dict[str, Any]:
        """
        检查是否可以执行一次预估成本的外部调用。
        如果剩余预算不足，返回拒绝信号。
        """
        status = self.budget_status()
        if status["level"] == "critical":
            return {
                "allowed": False,
                "reason": f"预算严重不足：已用 {status['total_cost']:.4f} / {status['budget']:.2f} 元",
                "status": status,
            }
        if status["remaining"] < estimated_cost:
            return {
                "allowed": False,
                "reason": f"预算不足：剩余 {status['remaining']:.4f} 元，预估需 {estimated_cost:.4f} 元",
                "status": status,
            }
        return {
            "allowed": True,
            "reason": "预算充足",
            "status": status,
        }


if __name__ == "__main__":
    monitor = CostMonitor()
    # 模拟记录
    monitor.record("deepseek-chat", 1500, 800, "测试成本监控")
    monitor.record("deepseek-v4-pro", 2000, 1200, "复杂架构任务")
    print("预算状态：", monitor.budget_status())
    print("检查是否可调用：", monitor.check_budget(estimated_cost=0.01))
