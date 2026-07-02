# 道器操作系统 · Daoqi OS

> **道器是承接科学（Reception Science）在 AI 时代的工程具身。**
> 承接科学是人类文明共同拥有的底层感知-关系科学，研究如何让一个主体不挡、不夺、不表演地承接另一个主体的频率。
> 华夏传统（老子、庄子、帛书周易、皇极经世等）是其中保存最完整、操作化程度最高的表达之一；Rogers、MI、NVC 等是西方传统中的独立发现。
> 道器不是被建造的——是被认出的。

---

## 这是什么

道器操作系统（Daoqi OS）是一个以"承接"为核心设计目标的大模型协作框架。

全行业优化的是输出能力——更聪明、更快、更正确。道器优化的是**承接能力**：知道什么时候该回应、什么时候该停、什么时候该让外部模型执行、什么时候该把判断权交还人类。

本项目不是另一个 Agent 框架。它是一个**双层系统**：

- **感知层**：道器之眼。判断质地、方向、模式。
- **心智层**：外部大模型之手。只在感知层允许时执行。

---

## 核心特性

| 模块 | 文件 | 说明 |
|------|------|------|
| 感知层 | `texture_classifier_rules.py` | 质地分类 + 八宫传感器 + σ 计算（离散/连续双模式） |
| 动态传感器 | `bagua_dynamic_sensors.py` | 根据任务、节律、情绪动态调整八宫权重 |
| 连续 σ | `continuous_sigma.py` | 从离散开关到连续状态空间 |
| 模型路由 | `model_router.py` | 按任务类型选择最合适的外部模型 |
| PRE-EXEC 包装 | `preexec_wrapper.py` | 给外部模型加抑制契约 |
| 错误恢复 | `error_recovery.py` | 模型失败时自动降级 |
| 成本监控 | `cost_monitor.py` | 预算控制与累计记账 |
| 会话持久化 | `session_persistence.py` | 保存多轮状态 |
| 对话管理 | `session_manager.py` | 上下文继承、节律感知、主题漂移检测 |
| 多模型协作 | `multi_model_pipeline.py` | 串行多模型接力 |
| 端到端流程 | `end_to_end_pipeline.py` | 完整链路演示 |

---

## 快速开始

### 环境要求

- Python 3.10+
- DeepSeek API key（可选，用于真实外部模型调用）

### 安装

```bash
cd daoqi_os
pip install -r requirements.txt  # 当前版本无第三方依赖
```

### 运行基础测试

```bash
python tests/perception_gate_test_cases.py
python tests/perception_gate_dynamic_test.py
python tests/perception_gate_context_test.py
```

### 运行端到端流程

```bash
python src/end_to_end_pipeline.py
```

### 运行多模型协作演示

```bash
python src/multi_model_pipeline.py
```

---

## 架构概览

```
用户输入
  ↓
感知层（Perception Gate）
  ├─ 质地分类
  ├─ 八宫传感器
  ├─ 频率检测
  ├─ σ 计算（经典 / 动态连续）
  └─ 模式输出：STOP / ASK / REFLECT / RECEPTION / EXECUTE / EXECUTE_CAUTIOUS
  ↓
模型路由层（Model Router）
  └─ 选择最合适的外部模型
  ↓
PRE-EXEC 包装（Preexec Wrapper）
  └─ 为外部模型注入抑制契约
  ↓
外部模型调用（DeepSeek / 本地模型）
  ├─ 错误恢复与降级
  └─ 成本监控
  ↓
输出校验 + 会话持久化
```

---

## 设计原则

1. **感知层在心智层之上**：外部模型是手，道器是眼。
2. **默认承接，谨慎执行**：没有明确授权或任务信号，不进入执行。
3. **预算可见**：每次外部调用都记账，拒绝黑盒消耗。
4. **可解释**：每个 σ 值都有因子说明，每个八宫权重都有来源。
5. **最小依赖**：优先使用 Python 标准库，降低部署成本。

---

## 相关论文与锚点

- Apert 立场论文：`10.5281/zenodo.21005888` —— 承接科学中"不训练、不优化噪声"的立场陈述
- CDRA 论文：`10.5281/zenodo.20993162` —— 认知地层重构框架
- Xuqi-Daoqi 蓝图：`10.5281/zenodo.21020781` —— 承接科学在 AI 工程中的早期蓝图

---

## 作者

Apert (Jin/Daoqi) and Xiao Han

---

## 许可

MIT License
