#!/usr/bin/env python3
"""HP Indigo 对开数码印刷报价计算器。

用法:
    python3 quote.py <w> <h> <p> <copies> <cover> <inner> <lamination> <binding>

参数:
    w, h        成品尺寸(mm)，如 210 297
    p           总页数(P，含封面 4P)
    copies      本数
    cover       封面纸张: <克重>-<copper|woodfree|card|self>-<double|single>，如 250-copper-double
    inner       内文纸张: 同上格式，如 157-copper-double
    lamination  none | matte | glossy
    binding     saddle | glue | lock | hard-nail | hard-butterfly | hard-lock

无第三方依赖，仅用标准库。
"""
import sys
import math

SHEET_W, SHEET_H = 510, 740          # HP 对开打印面积
BLEED = 3                             # 出血：上下左右各 3mm
COVER_P = 4                           # 封面固定 4P
LAM_PRICE = 0.5                       # 覆膜 元/张·对开

PAPER_NAME = {
    'copper': '铜版纸', 'woodfree': '胶版纸', 'card': '白卡纸', 'self': '自带纸',
}
# 单价：元/张·对开，(双面, 单面)
PAPERS = {
    'copper': {105: (1.6, 1.1), 128: (1.6, 1.2), 157: (1.6, 1.1),
               200: (1.9, 1.3), 250: (2.0, 1.4), 300: (2.2, 1.5)},
    'woodfree': {80: (1.6, 1.1), 100: (1.6, 1.1), 120: (1.6, 1.1)},
    'card': {230: (2.3, 1.6), 250: (2.4, 1.7), 300: (2.6, 1.8)},
}
LAM_NAME = {'none': '', 'matte': '亚膜', 'glossy': '亮膜'}
BIND_NAME = {
    'saddle': '骑马订', 'glue': '胶订（胶钉）', 'lock': '锁线胶装',
    'hard-nail': '硬壳打钉精装', 'hard-butterfly': '硬壳蝴蝶精装',
    'hard-lock': '硬壳锁线精装',
}
EVEN_BIND = {'saddle', 'lock', 'hard-nail', 'hard-butterfly', 'hard-lock'}
STEP_BIND = {
    'lock': (10, 8, 6, 5), 'hard-nail': (20, 15, 10, 8),
    'hard-butterfly': (20, 15, 10, 9), 'hard-lock': (20, 15, 10, 9),
}


def parse_spec(s):
    parts = s.split('-')
    if parts[0] == 'self':
        return 'self', 0, parts[1]
    return parts[1], int(parts[0]), parts[2]   # 格式 <克重>-<类型>-<面>，如 250-copper-double


def paper_price(typ, gram, side):
    if typ == 'self':
        return 2.0 if side == 'double' else 1.0   # 自带纸双面 = 单面 × 2
    d, s = PAPERS[typ][gram]
    return d if side == 'double' else s


def per_side_pages(w, h, binding):
    """出血后尺寸在对开 510x740 上每面能排几个 P；骑马订/锁线必须取偶数。"""
    bw, bh = w + 2 * BLEED, h + 2 * BLEED
    v = (SHEET_W // bw) * (SHEET_H // bh)   # 竖排
    r = (SHEET_W // bh) * (SHEET_H // bw)   # 旋转 90°
    if binding in EVEN_BIND:
        cands = [x for x in (v, r) if x % 2 == 0]
        return (max(cands) if cands else max(v, r)), bw, bh
    return max(v, r), bw, bh


def sheets(p_total, copies, per_side):
    """对开张数：双面每张 = per_side*2 个 P；单面印刷纸照算（张数同双面）。"""
    return math.ceil(p_total * copies / (per_side * 2))


def step_price(seq, n):
    if n <= 20:
        return seq[0]
    if n <= 49:
        return seq[1]
    if n <= 99:
        return seq[2]
    return seq[3]


def bind_cost(binding, copies, inner_type):
    if binding == 'saddle':
        return 0.5 * copies
    if binding == 'glue':
        return (1.5 if inner_type == 'copper' else 1.0) * copies  # 铜版胶钉/胶版胶钉
    return step_price(STEP_BIND[binding], copies) * copies


def fmt(v):
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f'{v:.2f}'.rstrip('0').rstrip('.')


def main():
    if len(sys.argv) < 9:
        print('usage: quote.py w h p copies cover inner lamination binding')
        sys.exit(1)
    w, h, p, copies = (int(sys.argv[i]) for i in range(1, 5))
    cover, inner, lam, binding = sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8]

    c_type, c_gram, c_side = parse_spec(cover)
    i_type, i_gram, i_side = parse_spec(inner)
    per_side, bw, bh = per_side_pages(w, h, binding)

    cover_sheets = sheets(COVER_P, copies, per_side)
    inner_p = p - COVER_P
    inner_sheets = sheets(inner_p, copies, per_side)

    cp = paper_price(c_type, c_gram, c_side)
    ip = paper_price(i_type, i_gram, i_side)
    cover_cost = cover_sheets * cp
    inner_cost = inner_sheets * ip
    print_cost = cover_cost + inner_cost

    lam_cost = cover_sheets * LAM_PRICE if lam != 'none' else 0.0
    bind = bind_cost(binding, copies, i_type)
    finish_cost = lam_cost + bind

    total = print_cost + finish_cost

    side_cn = {'double': '双面', 'single': '单面'}

    print('📋 原始规格')
    print(f'| 成品尺寸 | {w} × {h} mm（出血后 {bw}×{bh}） |')
    print(f'| 装订方式 | {BIND_NAME[binding]} |')
    print(f'| 总页数 | {p}P（封面 {COVER_P}P + 内文 {inner_p}P） |')
    print(f'| 封面 | {c_gram}g {PAPER_NAME[c_type]}，{side_cn[c_side]}印刷{LAM_NAME[lam]} |')
    print(f'| 内文 | {i_gram}g {PAPER_NAME[i_type]}，{side_cn[i_side]}印刷 |')
    print(f'| 数量 | {copies} 本 |')
    print(f'| 打印幅面 | HP 对开 {SHEET_W} × {SHEET_H} mm（{per_side}P/面） |')
    print()
    print('📄 印刷环节')
    print('| 环节 | 对开张数 | 单/双面 | 单价 | 金额 |')
    print(f'| 封面打印（{c_gram}g {PAPER_NAME[c_type]}） | {cover_sheets} 张 | {side_cn[c_side]} | {fmt(cp)} 元/张 | {fmt(cover_cost)} 元 |')
    print(f'| 内文打印（{i_gram}g {PAPER_NAME[i_type]}） | {inner_sheets} 张 | {side_cn[i_side]} | {fmt(ip)} 元/张 | {fmt(inner_cost)} 元 |')
    print(f'| **印刷小计** | **{cover_sheets + inner_sheets} 张** | | | **{fmt(print_cost)} 元** |')
    print()
    print('🛠 后期')
    print('| 项目 | 数量 | 单价 | 金额 |')
    if lam != 'none':
        print(f'| 覆膜（{LAM_NAME[lam]}） | {cover_sheets} 张对开 | {fmt(LAM_PRICE)} 元/张 | {fmt(lam_cost)} 元 |')
    print(f'| {BIND_NAME[binding]} | {copies} 本 | {fmt(bind / copies)} 元/本 | {fmt(bind)} 元 |')
    print(f'| **后期小计** | | | **{fmt(finish_cost)} 元** |')
    print()
    print(f'💰 **总计：{fmt(total)} 元**（单本 {fmt(total / copies)} 元）')


if __name__ == '__main__':
    main()
