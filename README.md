# print-quote-skill

HP Indigo 对开数码印刷报价 QwenPaw agent skill（💰）。适用于骑马订 / 胶订 / 锁线胶装 / 精装四类装订的报价计算。

## 文件

- `SKILL.md` — 技能说明：计价口径、价格表结构、输出模板
- `scripts/quote_xlsx.py` — 报价计算脚本（**价格从 xlsx 表格读取，改表即改价**）
- `scripts/prices_template.xlsx` — **空价格表模板**，表头与克重行已建好、价格留空，复制后填价即可使用

## 快速开始

```bash
pip install openpyxl
python3 scripts/quote_xlsx.py scripts/prices_template.xlsx 210 297 24 10 250-copper-double 157-copper-double matte saddle
```

参数：`<价格表.xlsx> 成品宽mm 成品高mm 总P数 本数 封面纸张 内文纸张 覆膜 装订方式`

纸张格式 `<克重>-<类型(copper/woodfree/card/self)>-<double/single>`（自带纸写 `self-single`）；覆膜 `none|matte|glossy`；装订 `saddle|glue|lock|hard-nail|hard-butterfly|hard-lock`。

## 价格表结构（prices_template.xlsx）

| 位置 | 内容 |
|---|---|
| A~C 列 | 铜版：克重 + 双面/单面单价（元/张·对开） |
| D~F 列 | 胶版纸：克重 + 双面/单面单价 |
| G~I 列 | 白卡纸：克重 + 双面/单面单价 |
| J 列 | 自带纸单面价 |
| K 列 | 自带纸双面价（可选；不填则按单面 ×2） |
| D8 / E8 / F8 | 骑马钉 / 铜版胶钉 / 胶版胶钉（元/本） |
| E10 | 覆膜单价（元/张·对开） |
| 14~17 行 | 精装阶梯价（1-20 / 21-49 / 50-99 / 100本以上） |

## 计价口径摘要

- 1 张对开纸 = 8P（每面 4P）；双面价 = 每张对开纸印双面的价格
- 出血：成品尺寸上下左右各 +3mm 后拼版；HP 对开打印面积 510×740mm
- 单面印刷纸照算（张数与双面相同），仅单价换单面价
- 覆膜按封面对开张数计；骑马钉/胶钉按本；精装按本数阶梯

## 让其他 Agent 使用（安装调用）

安装后技能名为 **算印刷报价**（取自 `SKILL.md` frontmatter 的 `name`）。

### 方式一：CLI 安装（推荐）

需要在能访问 GitHub 的环境执行（本机已运行 QwenPaw 服务即可）：

```bash
# 1. 查看有哪些 agent，获取目标 agent id
qwenpaw agents list

# 2. 直接安装到指定 agent 的 workspace 并启用（最简方式）
qwenpaw skills install https://github.com/forwilson2-coder/print-quote-skill \
  --agent-id <AGENT_ID> --enable

# 3. 确认已安装且启用
qwenpaw skills list --agent-id <AGENT_ID>
```

例如，把技能装给当前环境里的 `QwenPaw_QA_Agent_0.2`：

```bash
qwenpaw skills install https://github.com/forwilson2-coder/print-quote-skill \
  --agent-id QwenPaw_QA_Agent_0.2 --enable
```

如果只想装进**本地技能池**（之后按需给某个 workspace 开启）：

```bash
qwenpaw skills install https://github.com/forwilson2-coder/print-quote-skill
qwenpaw skills config --agent-id <AGENT_ID>   # 交互式勾选启用
```

### 方式二：手动放置

```bash
git clone https://github.com/forwilson2-coder/print-quote-skill
# 把 SKILL.md 和 scripts/ 放到目标 agent workspace 的 skills/算印刷报价/ 下
```

然后在目标 workspace 的 `skill.json` 的 `"skills"` 对象里登记（`enabled` 置 `true`）：

```json
"算印刷报价": {
  "enabled": true,
  "channels": ["all"],
  "source": "customized",
  "metadata": {
    "name": "算印刷报价",
    "description": "Use this skill when the user asks to 算印刷报价/算价格/报价 for HP Indigo 对开数码印刷 (骑马订/胶订/锁线胶装/精装). Inputs: 成品尺寸, 总P数, 封面内文纸张克重与单双面, 覆膜, 本数, 装订方式, 价格表xlsx. Output: formatted quote (原始规格→印刷环节→后期→总计).",
    "emoji": "💰"
  },
  "requirements": {"require_bins": [], "require_envs": []},
  "config": {}
}
```

### 依赖

- `openpyxl`：`pip install openpyxl`（`quote_xlsx.py` 读取 xlsx 用，其余为 Python 标准库）

### 调用方式

装好后，在该 agent 的对话里说「**算印刷报价 / 算价格 / 报个价**」并给出规格即可：
成品尺寸、总 P 数、本数、封面/内文纸张（克重+铜版/胶版/白卡/自带+单面/双面）、是否覆膜、装订方式。价格数据不齐时 agent 会主动向你补充询问。

> ⚠️ 仓库里的 `prices_template.xlsx` 是**空模板**（待填价格格已标红），安装后请复制一份填上你自己的价格表再使用。价格表通常放在 agent workspace 的 `media/` 目录，如 `media/hp对开报价.xlsx`。