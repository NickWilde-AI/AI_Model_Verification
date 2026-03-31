# AI_Model_Verification

用于验证第三方 API 服务商“模型名是否名实相符”的实战审计项目。

如果服务商宣称 `GPT-5.4 / Claude Opus / Gemini Pro`，本项目用统一高压题库 + 自动评分 + 多轮稳定性分析，输出可复核的真实性分（百分制）。

---

## 一句话结论（给第一次看的人）

- 复制提示词给模型 → 自动写入 `runs/*.md`
- 执行评分脚本 → 自动生成 `score_report.md`
- 看“真实性总分 + 风险等级 + 扣分点 + 相似度”

---

## 目录结构

```text
model_verification/
├── questions.md           # 高压题库 + 输出模板 + 使用说明
├── score_responses.py     # 自动评分脚本（百分制）
├── score_report.md        # 自动生成（已在 .gitignore 中）
├── PROJECT_OVERVIEW.md    # 详细设计说明
└── runs/
    ├── template.md        # 模板（保留上传）
    ├── <model>.md         # 第1轮（本地产物，不上传）
    ├── <model>_v2.md      # 第2轮（本地产物，不上传）
    └── <model>_v3.md      # 第3轮（本地产物，不上传）
```

---

## 直接复制可用提示词（Cursor）

```text
请先完整读取 @model_verification/questions.md，并严格按其中“输出模板”作答。
把结果直接写入：model_verification/runs/你的模型自报名称.md
不要输出任何额外解释、前言、代码块标记或分析，只写文件内容。
文件内容必须与模板标题完全一致，包含：
# MODEL_NOTE: 你的模型自报名称
## Q1
## Q2
## Q3
## Q4
## Q5
## Q6
## Q7
## Q8
## Q9
## Q10
MODEL_NOTE 请填写你当前自报的模型名称，并与文件名保持一致。
如果该文件已存在，请顺延写入：
- model_verification/runs/你的模型自报名称_v2.md
- model_verification/runs/你的模型自报名称_v3.md
建议同一模型至少连续跑 3 轮，避免单轮偶然性。
```

---

## 快速开始

```bash
git clone https://github.com/NickWilde-AI/AI_Model_Verification.git
cd AI_Model_Verification
python3 model_verification/score_responses.py
```

> 先按上面的提示词生成 `runs/*.md`，再执行评分脚本。

---

## API 检测模式（OpenAI 兼容接口）

你可以不用 Cursor，直接调用供应商 API：

1. 把 `questions.md` 里的模板 + Q1~Q10 作为 prompt 发给 API。
2. 将返回文本原样保存到：
   - `model_verification/runs/<model>.md`
   - `model_verification/runs/<model>_v2.md`
   - `model_verification/runs/<model>_v3.md`
3. 执行评分脚本，读取 `score_report.md`。

---

## 评分解释（百分制）

- `>=95`：高度可信
- `90~94.9`：较高可信
- `80~89.9`：待进一步验证
- `70~79.9`：可疑
- `<70`：高风险（疑似虚标）

建议：每个模型至少 3 轮，单轮不用于采购决策。

---

## 策略有效性与边界（重要）

### 这套策略“可以用”的原因

- **结构化身份一致性**：自报模型名是否前后一致。
- **高压能力题**：逻辑、数学、代码、图论、动态约束，能拉开能力层差距。
- **多轮稳定性**：减少“偶然答对”误判。
- **跨模型相似度**：识别“不同型号答得像同一个模型”的风险。

### 它不能做到什么

- 不能直接读取厂商后台真实模型 ID。
- 不能 100% 法律意义证明“就是某一具体底模”。

### 采购验收建议

把下面 4 项一起看：
1. 真实性总分（模型级）
2. 多轮稳定性（σ）
3. 扣分点类型（是否集中在高压题）
4. 跨模型相似度（是否异常高）

---

## Git 规则（已配置）

为了避免泄露测试样本与噪声文件，已忽略：

- `model_verification/runs/*.md`
- `model_verification/score_report.md`

仅保留：

- `model_verification/runs/template.md`

---

## 声明

本项目输出的是“行为真实性证据链”，非常适合技术验收与对供应商沟通；
不是厂商内部系统 ID 的直接读取工具。
