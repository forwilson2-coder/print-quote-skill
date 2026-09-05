#!/usr/bin/env python3
"""HP Indigo 对开数码印刷报价计算器（价格从 xlsx 表格读取）。

价格不再硬编码/写 JSON，直接读取 HP 对开报价表 xlsx（改表格即改价）。
表格结构（Sheet1，见 media/*hp对开报价.xlsx）：
  第2行表头：A=铜版 B/C=双/单面，D=胶版纸 E/F=双/单面，G=白卡 H/I=双/单面，J=自带纸单面
  第3行起：  "105g" 克重行，同行取双面/单面价格
  后期：     D8=骑马钉，E8=铜版胶钉，F8=胶版胶钉，E10=覆膜(亮/哑/相膜同价)
  精装：     第13行档位表头(C/E/F/G)，14~17行=锁线/硬壳打钉/硬壳蝴蝶/硬壳锁线 阶梯价

用法:
    python3 quote_xlsx.py <报价表.xlsx> <w> <h> <p> <copies> <cover> <inner> <lamination> <binding>

参数:
    报价表.xlsx  价格表文件路径（结构如上）
    w, h         成品尺寸(mm)，如 210 297
    p            总页数(P，含封面 4P)
    copies       本数
    cover        封面纸张: <克重>-<copper|woodfree|card|self>-<double|single>，如 250-copper-double
    inner        内文纸张: 同上格式，如 157-copper-double
    lamination   none | matte | glossy（价格同取表格覆膜单价）
    binding      saddle | glue | lock | hard-nail | hard-butterfly | hard-lock

依赖: openpyxl（标准库之外的唯一依赖）。其余仅用标准库。
"""
import sys
import math

import openpyxl

SHEET_W, SHEET_H = 510, 740          # HP 对开打印面积（xlsx 无此字段时用默认）
BLEED = 3                             # 出血：上下左右各 3mm
COVER_P = 4                           # 封面固定 4P

TYPE_NAMES = {'copper': '铜版纸', 'woodfree': '胶版纸', 'card': '白卡纸', 'self': '自带纸'}
BIND_NAME = {
    'saddle': '骑马订', 'glue': '胶订（胶钉）', 'lock': '锁线胶装',
    'hard-nail': '硬壳打钉精装', 'hard-butterfly': '硬壳蝴蝶精装',
    'hard-lock': '硬壳锁线精装',
}
EVEN_BIND = {'saddle', 'lock', 'hard-nail', 'hard-butterfly', 'hard-lock'}
HARD_ROW = {'lock': 14, 'hard-nail': 15, 'hard-butterfly': 16, 'hard-lock': 17}
LAM_NAME = {'none': '', 'matte': '亚膜', 'glossy': '亮膜'}


def cell(ws, col, row):
    v = ws[f'{col}{row}'].value
    return v


def num(v):
    if v is None or v == '':
        return None
    try:
        return float(str(v).strip())
    except ValueError:
        return None


def parse_gram(s):
    if s is None:
        return None
    t = str(s).strip().lower()
    if t.endswith('g'):
        t = t[:-1]
    try:
        return int(t)
    except ValueError:
        return None


def load_price_table(path):
    """读取 xlsx 报价表，返回价格字典。"""
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active

    papers = {}
    # 纸张组：(克重列, 双面列, 单面列, 纸种key)
    for wcol, dcol, scol, typ in (('A', 'B', 'C', 'copper'),
                                  ('D', 'E', 'F', 'woodfree'),
                                  ('G', 'H', 'I', 'card')):
        prices = {}
        for r in range(3, 9):
            gram = parse_gram(cell(ws, wcol, r))
            if gram is None:
                continue
            d = num(cell(ws, dcol, r))
            s = num(cell(ws, scol, r))
            if d is not None and s is not None:
                prices[gram] = (d, s)
        papers[typ] = prices

    self_single = num(cell(ws, 'J', 3))          # 自带纸单面
    papers['self'] = self_single

    return {
        'sheet_w': SHEET_W, 'sheet_h': SHEET_H, 'bleed': BLEED,
        'papers': papers,
        'saddle': num(cell(ws, 'D', 8)),
        'glue_copper': num(cell(ws, 'E', 8)),
        'glue_woodfree': num(cell(ws, 'F', 8)),
        'lamination': num(cell(ws, 'E', 10)),
        'hard': {key: [num(cell(ws, c, row)) for c in ('C', 'E', 'F', 'G')]
                 for key, row in HARD_ROW.items()},
    }


def paper_price(tbl, typ, gram, side):
    if typ == 'self':
        return tbl['papers']['self'] * 2 if side == 'double' else tbl['papers']['self']
    d, s = tbl['papers'][typ][gram]
    return d if side == 'double' else s


def per_side_pages(tbl, w, h, binding):
    bw, bh = w + 2 * tbl['bleed'], h + 2 * tbl['bleed']
    v = (tbl['sheet_w'] // bw) * (tbl['sheet_h'] // bh)
    r = (tbl['sheet_w'] // bh) * (tbl['sheet_h'] // bw)
    if binding in EVEN_BIND:
        cands = [x for x in (v, r) if x % 2 == 0]
        return (max(cands) if cands else max(v, r)), bw, bh
    return max(v, r), bw, bh


def sheets(p_total, copies, per_side):
    return math.ceil(p_total * copies / (per_side * 2))


def step_price(seq, n):
    if n <= 20:
        return seq[0]
    if n <= 49:
        return seq[1]
    if n <= 99:
        return seq[2]
    return seq[3]


def bind_cost(tbl, binding, copies, inner_type):
    if binding == 'saddle':
        return tbl['saddle'] * copies
    if binding == 'glue':
        return (tbl['glue_copper'] if inner_type == 'copper' else tbl['glue_woodfree']) * copies
    return step_price(tbl['hard'][binding], copies) * copies


def parse_spec(s):
    parts = s.split('-')
    if parts[0] == 'self':
        return 'self', 0, parts[1]
    return parts[1], int(parts[0]), parts[2]   # 格式 <克重>-<类型>-<面>


def fmt(v):
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f'{v:.2f}'.rstrip('0').rstrip('.')


def main():
    if len(sys.argv) < 10:
        print('usage: quote_xlsx.py <报价表.xlsx> w h p copies cover inner lamination binding')
        sys.exit(1)
    tbl = load_price_table(sys.argv[1])
    w, h, p, copies = (int(sys.argv[i]) for i in range(2, 6))
    cover, inner, lam, binding = sys.argv[6], sys.argv[7], sys.argv[8], sys.argv[9]

    c_type, c_gram, c_side = parse_spec(cover)
    i_type, i_gram, i_side = parse_spec(inner)
    per_side, bw, bh = per_side_pages(tbl, w, h, binding)

    cover_sheets = sheets(COVER_P, copies, per_side)
    inner_p = p - COVER_P
    inner_sheets = sheets(inner_p, copies, per_side)

    cp = paper_price(tbl, c_type, c_gram, c_side)
    ip = paper_price(tbl, i_type, i_gram, i_side)
    cover_cost = cover_sheets * cp
    inner_cost = inner_sheets * ip
    print_cost = cover_cost + inner_cost

    lam_cost = cover_sheets * tbl['lamination'] if lam != 'none' else 0.0
    bind = bind_cost(tbl, binding, copies, i_type)
    finish_cost = lam_cost + bind
    total = print_cost + finish_cost

    side_cn = {'double': '双面', 'single': '单面'}
    print('📋 原始规格')
    print(f'| 成品尺寸 | {w} × {h} mm（出血后 {bw}×{bh}） |')
    print(f'| 装订方式 | {BIND_NAME[binding]} |')
    print(f'| 总页数 | {p}P（封面 {COVER_P}P + 内文 {inner_p}P） |')
    print(f'| 封面 | {c_gram}g {TYPE_NAMES[c_type]}，{side_cn[c_side]}印刷{LAM_NAME[lam]} |')
    print(f'| 内文 | {i_gram}g {TYPE_NAMES[i_type]}，{side_cn[i_side]}印刷 |')
    print(f'| 数量 | {copies} 本 |')
    print(f'| 打印幅面 | HP 对开 {tbl["sheet_w"]} × {tbl["sheet_h"]} mm（{per_side}P/面） |')
    print('📄 印刷环节')
    print('| 环节 | 对开张数 | 单/双面 | 单价 | 金额 |')
    print(f'| 封面打印（{c_gram}g {TYPE_NAMES[c_type]}） | {cover_sheets} 张 | {side_cn[c_side]} | {fmt(cp)} 元/张 | {fmt(cover_cost)} 元 |')
    print(f'| 内文打印（{i_gram}g {TYPE_NAMES[i_type]}） | {inner_sheets} 张 | {side_cn[i_side]} | {fmt(ip)} 元/张 | {fmt(inner_cost)} 元 |')
    print(f'| **印刷小计** | **{cover_sheets + inner_sheets} 张** | | | **{fmt(print_cost)} 元** |')
    print('🛠 后期')
    print('| 项目 | 数量 | 单价 | 金额 |')
    if lam != 'none':
        print(f'| 覆膜（{LAM_NAME[lam]}） | {cover_sheets} 张对开 | {fmt(tbl["lamination"])} 元/张 | {fmt(lam_cost)} 元 |')
    print(f'| {BIND_NAME[binding]} | {copies} 本 | {fmt(bind / copies)} 元/本 | {fmt(bind)} 元 |')
    print(f'| **后期小计** | | | **{fmt(finish_cost)} 元** |')
    print(f'💰 **总计：{fmt(total)} 元**（单本 {fmt(total / copies)} 元）')


if __name__ == '__main__':
    main()