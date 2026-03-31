# AI_Model_Verification

一个用于**验证第三方 API 服务商模型真实性**的审计项目。

当服务商声称提供的是 `GPT-5.4 / Claude Opus / Gemini Pro` 等高端模型时，本项目通过统一题库、多轮采样和百分制评分，帮助你判断：

- 模型是否“名实相符”
- 是否存在“低代模型换壳高价售卖”风险
- 多模型之间是否疑似同源

## 项目结构

```text
model_verification/
├── questions.md          # 高压题库（Q1~Q10）与执行说明
├── score_responses.py    # 自动评分脚本（百分制）
├── score_report.md       # 自动生成的评分报告
├── PROJECT_OVERVIEW.md   # 项目说明（详细版）
└── runs/
    ├── template.md
    ├── <model>.md
    ├── <model>_v2.md
    └── <model>_v3.md
```

## 适用场景

- 你在国内 API 服务商购买了“高规格模型”
- 你怀疑实际交付可能是旧模型或降配模型
- 你需要一套可复现、可量化、可对比的验收流程

## 快速开始

1. 在 Cursor 切换到待测模型。
2. 让模型读取 `model_verification/questions.md` 并按模板写入 `model_verification/runs/*.md`。
3. 每个模型建议至少跑 3 轮（`_v2` / `_v3`），避免单轮偶然性。
4. 运行评分脚本：

```bash
python3 model_verification/score_responses.py
```

5. 查看结果：
- 终端输出：模型真实性分（百分制）
- 报告文件：`model_verification/score_report.md`

## 评分结果解释（简版）

- `>=95`：高度可信
- `90~94.9`：较高可信
- `80~89.9`：待进一步验证
- `70~79.9`：可疑
- `<70`：高风险（疑似虚标）

## 注意事项

- 本项目提供的是**行为真实性证据**，不是厂商后台内部 model ID 的直接证明。
- 采购验收建议基于：多轮稳定性 + 真实性总分 + 扣分细节综合判断。

---

如需对外沟通（向服务商投诉或申诉），建议附上：
- `runs/` 原始回答文件
- `score_report.md`
- 本仓库版本号（commit hash）
