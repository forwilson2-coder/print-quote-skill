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
| J 列 | 自带纸单面价（双面自动 ×2） |
| D8 / E8 / F8 | 骑马钉 / 铜版胶钉 / 胶版胶钉（元/本） |
| E10 | 覆膜单价（元/张·对开） |
| 14~17 行 | 精装阶梯价（1-20 / 21-49 / 50-99 / 100本以上） |

## 计价口径摘要

- 1 张对开纸 = 8P（每面 4P）；双面价 = 每张对开纸印双面的价格
- 出血：成品尺寸上下左右各 +3mm 后拼版；HP 对开打印面积 510×740mm
- 单面印刷纸照算（张数与双面相同），仅单价换单面价
- 覆膜按封面对开张数计；骑马钉/胶钉按本；精装按本数阶梯