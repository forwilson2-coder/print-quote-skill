# print-quote-skill

HP Indigo 对开数码印刷报价 QwenPaw agent skill（💰）。

## 文件

- `SKILL.md` — 完整规则、计价口径、输出模板与回归算例
- `scripts/quote.py` — 报价计算脚本（仅标准库），用法：
  ```
  python3 scripts/quote.py 210 297 24 10 250-copper-double 157-copper-double matte saddle
  ```
  （参数：成品宽高mm 总P数 本数 封面纸张 内文纸张 覆膜 装订方式；纸张格式 `<克重>-<类型(copper/woodfree/card/self)>-<double/single>`，覆膜 `none|matte|glossy`，装订 `saddle|glue|lock|hard-nail|hard-butterfly|hard-lock`）
- `scripts/quote.json` — `run_tool_batch` 批处理入口（QwenPaw 环境内使用）

## 说明

报价体系基于 HP 对开（510×740mm）数码印刷实际行情，含骑马订/胶订/锁线胶装/精装四类装订计价。
