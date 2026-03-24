#!/usr/bin/env python3
"""
缠论中枢、背驰、三类买卖点模块 v2.0
功能：
  - 中枢识别（Chan.zhongshu）
  - 背驰判断（Chan.beichi）
  - 三类买卖点（Chan.maidian）
  - 综合评分（Chan.score）

用法：
  python3 chan.py 002929              # 分析润建股份
  python3 chan.py 002929 --days 120  # 分析最近120天
  python3 chan.py 002929 --raw        # 显示原始K线
"""

import requests
import sys
from datetime import datetime

# ========== 东方财富API ==========
def get_kline(secid, days=120):
    """获取日K线（前复权）- 使用腾讯财经API"""
    market = 'sh' if secid.startswith('1.') else 'sz'
    code = secid.split('.')[1]
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
    params = {
        '_var': 'kline_dayhfq',
        'param': f"{market}{code},day,2020-01-01,2050-12-31,{days},qfq"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        text = r.text
        import json as _json
        json_str = text[text.index('=') + 1:]
        data = _json.loads(json_str)
        raw = data.get('data', {}).get(f"{market}{code}", {}).get('qfqday', [])
        if not raw:
            raw = data.get('data', {}).get(f"{market}{code}", {}).get('day', [])
        result = []
        for line in raw:
            if len(line) >= 6:
                try:
                    result.append({
                        'date': line[0], 'open': float(line[1]), 'close': float(line[2]),
                        'high': float(line[3]), 'low': float(line[4]), 'volume': int(float(line[5]))
                    })
                except (ValueError, IndexError):
                    continue
        return result
    except Exception as e:
        print(f"❌ 数据获取失败: {e}")
        return []

def secid_of(symbol):
    """股票代码 → 东方财富secid"""
    s = symbol.strip()
    if s.startswith(('6', '5', '9', '7')):
        return f"1.{s}"
    return f"0.{s}"


# ========== 缠论核心算法 v1.0（笔段）==========

def resolve_inclusion(klines):
    """处理K线包含关系"""
    if len(klines) < 3:
        return list(klines)
    bars = [{'date': k['date'], 'open': k['open'], 'close': k['close'],
             'high': k['high'], 'low': k['low'], 'volume': k['volume']} for k in klines]
    if bars[1]['high'] > bars[0]['high'] and bars[1]['low'] >= bars[0]['low']:
        direction = 1
    elif bars[1]['high'] < bars[0]['high'] and bars[1]['low'] <= bars[0]['low']:
        direction = -1
    else:
        direction = 1 if bars[2]['high'] > bars[0]['high'] else -1
    result = [bars[0], bars[1]]
    i = 2
    while i < len(bars):
        prev = result[-1]; curr = bars[i]
        has_inclusion = (curr['high'] <= prev['high'] and curr['low'] >= prev['low']) or \
                        (curr['high'] >= prev['high'] and curr['low'] <= prev['low'])
        if not has_inclusion:
            result.append(curr); i += 1; continue
        merged = {}
        if direction == 1:
            merged['high'] = max(prev['high'], curr['high'])
            merged['low'] = max(prev['low'], curr['low'])
        else:
            merged['high'] = min(prev['high'], curr['high'])
            merged['low'] = min(prev['low'], curr['low'])
        merged['date'] = curr['date']
        merged['open'] = curr['open']
        merged['close'] = curr['close']
        merged['volume'] = curr['volume']
        result[-1] = merged
        i += 1
    return result

def find_fenxing(klines):
    """识别分型"""
    fenxings = []
    for i in range(1, len(klines) - 1):
        prev = klines[i - 1]; mid = klines[i]; nxt = klines[i + 1]
        if mid['high'] > prev['high'] and mid['high'] > nxt['high']:
            fenxings.append((i, 'top', mid))
        elif mid['low'] < prev['low'] and mid['low'] < nxt['low']:
            fenxings.append((i, 'bottom', mid))
    return fenxings

def identify_bi(klines):
    """识别笔"""
    if not klines or len(klines) < 5:
        return []
    resolved = resolve_inclusion(klines)
    if len(resolved) < 5:
        return []
    fenxings = find_fenxing(resolved)
    if len(fenxings) < 2:
        return []
    bis = []
    i = 0
    while i < len(fenxings) - 1:
        fx1_idx, fx1_type, fx1_bar = fenxings[i]
        fx2_idx, fx2_type, fx2_bar = fenxings[i + 1]
        mid_count = fx2_idx - fx1_idx - 1
        if fx1_type == 'bottom' and fx2_type == 'top':
            bi_type = 'up'; start_price = fx1_bar['low']; end_price = fx2_bar['high']
        elif fx1_type == 'top' and fx2_type == 'bottom':
            bi_type = 'down'; start_price = fx1_bar['high']; end_price = fx2_bar['low']
        else:
            i += 1; continue
        if mid_count < 3:
            i += 1; continue
        amp = (end_price - start_price) / start_price * 100
        bis.append({
            'type': bi_type, 'start_date': fx1_bar['date'], 'end_date': fx2_bar['date'],
            'start_idx': fx1_idx, 'end_idx': fx2_idx,
            'start_price': round(start_price, 2), 'end_price': round(end_price, 2),
            'amplitude': round(amp, 2), 'bars_count': mid_count + 2,
        })
        i += 1
    return bis

def identify_seg(bis):
    """识别线段（简化版）"""
    if not bis or len(bis) < 3:
        return []
    segs = []
    i = 0
    while i <= len(bis) - 3:
        direction = bis[i]['type']
        j = i + 1
        while j < len(bis) and bis[j]['type'] == direction:
            j += 1
        count = j - i
        if count >= 3:
            if direction == 'up':
                start_price = max(bis[k]['start_price'] for k in range(i, j))
                end_price = min(bis[k]['end_price'] for k in range(i, j))
            else:
                start_price = min(bis[k]['start_price'] for k in range(i, j))
                end_price = max(bis[k]['end_price'] for k in range(i, j))
            if (direction == 'up' and end_price > start_price) or \
               (direction == 'down' and end_price < start_price):
                amp = abs(end_price - start_price) / start_price * 100
                segs.append({
                    'type': direction, 'start_date': bis[i]['start_date'],
                    'end_date': bis[j-1]['end_date'], 'start_price': round(start_price, 2),
                    'end_price': round(end_price, 2), 'amplitude': round(amp, 2), 'bi_count': count,
                })
                i = j; continue
        i += 1
    return segs


# ========== 中枢识别 v2.0 ==========
def find_zhongshu(bis):
    """
    识别中枢。
    缠论规则：任意相邻笔的重叠区域构成中枢（简化版）。
    算法：
    - 遍历所有相邻笔对，如果重叠则形成中枢
    - 合并相邻重叠的中枢区间
    - 中枢方向 = 构成重叠的第一笔的方向
    """
    if not bis or len(bis) < 2:
        return []

    # Step 1: 找所有相邻笔对的重叠区间
    raw_zs = []
    for i in range(len(bis) - 1):
        b0, b1 = bis[i], bis[i+1]
        zg = max(b0['start_price'], b1['start_price'])
        zd = min(b0['end_price'], b1['end_price'])
        overlap = zg < zd
        if overlap:
            raw_zs.append({
                'start_bi_idx': i, 'end_bi_idx': i + 1,
                'start_date': b0['start_date'], 'end_date': b1['end_date'],
                'zg': round(zg, 2), 'zd': round(zd, 2),
                'range_width': round((zd - zg) / zd * 100, 2),
                'type': b0['type'],
            })

    if not raw_zs:
        return []

    # Step 2: 合并相邻重叠的中枢
    merged = []
    for z in raw_zs:
        if not merged:
            merged.append(z); continue
        prev = merged[-1]
        if z['zg'] <= prev['zd']:
            prev['zg'] = max(prev['zg'], z['zg'])
            prev['zd'] = min(prev['zd'], z['zd'])
            prev['end_bi_idx'] = z['end_bi_idx']
            prev['end_date'] = z['end_date']
            prev['range_width'] = round((prev['zd'] - prev['zg']) / prev['zd'] * 100, 2)
            continue
        merged.append(z)

    for idx, z in enumerate(merged):
        z['index'] = idx + 1
    return merged


# ========== MACD力度计算（用于背驰）==========
def _calc_ema(data, period):
    k_val = 2 / (period + 1)
    result = [data[0]]
    for d in data[1:]:
        result.append(d * k_val + result[-1] * (1 - k_val))
    return result

def calc_macd_for_bis(resolved_klines, bis):
    """
    计算每笔的MACD histogram面积作为力度指标。
    基于resolved klines计算（因为bi的索引引用resolved klines）。
    返回：{bi_index: {'area', 'amplitude', 'end_price', 'start_price'}}
    """
    if not resolved_klines or len(resolved_klines) < 35 or not bis:
        return {}
    closes = [k['close'] for k in resolved_klines]
    if len(closes) < 35:
        return {}
    ema12 = _calc_ema(closes, 12)
    ema26 = _calc_ema(closes, 26)
    dif_seq = [ema12[i] - ema26[i] for i in range(len(closes))]
    dea_seq = _calc_ema(dif_seq, 9)
    macd_seq = [2 * (dif_seq[i] - dea_seq[i]) for i in range(len(closes))]
    result = {}
    for idx, bi in enumerate(bis):
        si = bi['start_idx']
        ei = bi['end_idx']
        if si < 0 or ei >= len(macd_seq) or si >= len(macd_seq):
            continue
        area = sum(macd_seq[si:min(ei+1, len(macd_seq))])
        result[idx] = {
            'area': round(area, 4),
            'amplitude': bi['amplitude'],
            'end_price': bi['end_price'],
            'start_price': bi['start_price'],
        }
    return result


# ========== 背驰判断 ==========
def find_beichi(bis, zhongshu_list, macd_data, klines=None):
    """
    背驰判断（增强版）。
    模式A（标准）：离开中枢后连续两笔方向相同，比较力度
    模式B（宽松）：最近同方向两笔比较力度（允许中间隔一笔）

    底背驰：下降趋势中，价格创新低但力度衰减
    顶背驰：上升趋势中，价格创新高但力度衰减
    """
    if not bis or not macd_data:
        return []
    beichi_signals = []

    # 模式A：标准模式（要求完全连续）
    for z in zhongshu_list:
        z_end = z['end_bi_idx']
        direction = z['type']
        expected_leave_dir = 'down' if direction == 'up' else 'up'
        if z_end + 2 >= len(bis):
            continue
        b1 = bis[z_end + 1]
        b2 = bis[z_end + 2]
        if not (b1['type'] == b2['type'] == expected_leave_dir):
            continue
        idx1, idx2 = z_end + 1, z_end + 2
        d1 = macd_data.get(idx1)
        d2 = macd_data.get(idx2)
        if not d1 or not d2:
            continue
        area1 = abs(d1['area'])
        area2 = abs(d2['area'])
        amp1 = abs(d1['amplitude'])
        amp2 = abs(d2['amplitude'])
        if area2 == 0:
            continue
        bei_ratio = area1 / area2
        if expected_leave_dir == 'up':
            price_new_low = d2['end_price'] < d1['end_price']
            if price_new_low and (bei_ratio > 1.1 or (amp2/amp1 > 0.9 and bei_ratio > 1.2)):
                strength = round(min(bei_ratio / 2, 3.0), 2)
                beichi_signals.append({
                    'type': '底背驰', 'direction': 'up',
                    'bi_pair': (idx1, idx2), 'mode': 'A',
                    'price_before': d1['end_price'], 'price_after': d2['end_price'],
                    'area_before': round(area1, 4), 'area_after': round(area2, 4),
                    'amplitude_before': round(amp1, 2), 'amplitude_after': round(amp2, 2),
                    'bei_ratio': round(bei_ratio, 2), 'strength': strength,
                    'date': b2['end_date'], 'center_idx': z['index'],
                    'desc': f"标准背驰 | 价格↓{d2['end_price']}<{d1['end_price']}力度↓{bei_ratio:.1f}x(面积{area1:.2f}→{area2:.2f})"
                })
        else:
            price_new_high = d2['end_price'] > d1['end_price']
            if price_new_high and (bei_ratio > 1.1 or (amp2/amp1 > 0.9 and bei_ratio > 1.2)):
                strength = round(min(bei_ratio / 2, 3.0), 2)
                beichi_signals.append({
                    'type': '顶背驰', 'direction': 'down',
                    'bi_pair': (idx1, idx2), 'mode': 'A',
                    'price_before': d1['end_price'], 'price_after': d2['end_price'],
                    'area_before': round(area1, 4), 'area_after': round(area2, 4),
                    'amplitude_before': round(amp1, 2), 'amplitude_after': round(amp2, 2),
                    'bei_ratio': round(bei_ratio, 2), 'strength': strength,
                    'date': b2['end_date'], 'center_idx': z['index'],
                    'desc': f"标准背驰 | 价格↑{d2['end_price']}>{d1['end_price']}力度↓{bei_ratio:.1f}x(面积{area1:.2f}→{area2:.2f})"
                })

    # 模式B：宽松模式（最近同方向两笔，不要求连续）
    # 找最近连续或准连续同方向笔对
    if len(bis) >= 4:
        for i in range(len(bis) - 3):
            b_curr = bis[i]
            b_next = bis[i + 1]
            if b_curr['type'] != b_next['type']:
                continue
            # 找到同方向连续笔对，继续找下一对
            if i + 3 >= len(bis):
                continue
            b_next2 = bis[i + 2]
            b_next3 = bis[i + 3]
            if b_next2['type'] != b_next3['type'] or b_next2['type'] != b_curr['type']:
                continue
            # 比较 (b_curr,b_next) 和 (b_next2,b_next3) 的力度
            d1 = macd_data.get(i)
            d2 = macd_data.get(i + 1)
            d3 = macd_data.get(i + 2)
            d4 = macd_data.get(i + 3)
            if not all([d1, d2, d3, d4]):
                continue
            area1 = abs(d1['area']) + abs(d2['area'])
            area2 = abs(d3['area']) + abs(d4['area'])
            amp1 = abs(d1['amplitude']) + abs(d2['amplitude'])
            amp2 = abs(d3['amplitude']) + abs(d4['amplitude'])
            if area2 == 0:
                continue
            bei_ratio = area1 / area2
            direction = b_curr['type']

            if direction == 'down':
                # 底背驰：第二对末端价格更低
                price_after = min(d3['end_price'], d4['end_price'])
                price_before = min(d1['end_price'], d2['end_price'])
                if price_after < price_before and (bei_ratio > 1.2 or (amp2/amp1 > 0.8 and bei_ratio > 1.3)):
                    strength = round(min(bei_ratio / 2, 3.0), 2)
                    # 避免重复
                    existing = [b['desc'] for b in beichi_signals]
                    desc = f"宽松背驰 | 两波↓力度{bei_ratio:.1f}x | {price_before:.2f}→{price_after:.2f}(新低)"
                    if desc not in existing:
                        beichi_signals.append({
                            'type': '底背驰', 'direction': 'up',
                            'bi_pair': (i, i+3), 'mode': 'B',
                            'price_before': price_before, 'price_after': price_after,
                            'area_before': round(area1, 4), 'area_after': round(area2, 4),
                            'amplitude_before': round(amp1, 2), 'amplitude_after': round(amp2, 2),
                            'bei_ratio': round(bei_ratio, 2), 'strength': strength,
                            'date': b_next3['end_date'], 'center_idx': 0,
                            'desc': desc
                        })
            else:
                price_after = max(d3['end_price'], d4['end_price'])
                price_before = max(d1['end_price'], d2['end_price'])
                if price_after > price_before and (bei_ratio > 1.2 or (amp2/amp1 > 0.8 and bei_ratio > 1.3)):
                    strength = round(min(bei_ratio / 2, 3.0), 2)
                    existing = [b['desc'] for b in beichi_signals]
                    desc = f"宽松背驰 | 两波↑力度{bei_ratio:.1f}x | {price_before:.2f}→{price_after:.2f}(新高)"
                    if desc not in existing:
                        beichi_signals.append({
                            'type': '顶背驰', 'direction': 'down',
                            'bi_pair': (i, i+3), 'mode': 'B',
                            'price_before': price_before, 'price_after': price_after,
                            'area_before': round(area1, 4), 'area_after': round(area2, 4),
                            'amplitude_before': round(amp1, 2), 'amplitude_after': round(amp2, 2),
                            'bei_ratio': round(bei_ratio, 2), 'strength': strength,
                            'date': b_next3['end_date'], 'center_idx': 0,
                            'desc': desc
                        })

    # 按日期排序（最新的在前）
    beichi_signals.sort(key=lambda x: x['date'], reverse=True)
    return beichi_signals


# ========== 三类买卖点 ==========
def find_maidian(bis, zhongshu_list, beichi_signals, klines=None):
    """
    识别三类买卖点。
    1买：底背驰；2买：1买后回调不破新低；3买：中枢后回调不进入中枢
    1卖：顶背驰；2卖：1卖后反弹不创新高；3卖：中枢后反弹不进入中枢
    """
    if not bis or not zhongshu_list:
        return {'buy': [], 'sell': []}
    buy_points = []
    sell_points = []

    # === 第一类买卖点 ===
    for bc in beichi_signals:
        if bc['type'] == '底背驰':
            buy_points.append({
                'level': 1, 'name': '第一类买点(1买)',
                'date': bc['date'], 'price': bc['price_after'],
                'strength': bc['strength'], 'bei_ratio': bc['bei_ratio'],
                'center_idx': bc['center_idx'], 'desc': bc['desc'], 'type': 'buy'
            })
        elif bc['type'] == '顶背驰':
            sell_points.append({
                'level': 1, 'name': '第一类卖点(1卖)',
                'date': bc['date'], 'price': bc['price_after'],
                'strength': bc['strength'], 'bei_ratio': bc['bei_ratio'],
                'center_idx': bc['center_idx'], 'desc': bc['desc'], 'type': 'sell'
            })

    # === 第二类买卖点 ===
    for buy1 in list(buy_points):
        idx1 = None
        for j, bi in enumerate(bis):
            if bi['end_date'] >= buy1['date']:
                idx1 = j; break
        if idx1 is None or idx1 + 2 >= len(bis):
            continue
        for j in range(idx1, min(idx1 + 5, len(bis) - 1)):
            if bis[j]['type'] == 'down' and j + 1 < len(bis) and bis[j+1]['type'] == 'up':
                pullback_low = bis[j]['end_price']
                if pullback_low >= buy1['price'] * 0.97:
                    buy_points.append({
                        'level': 2, 'name': '第二类买点(2买)',
                        'date': bis[j]['end_date'], 'price': pullback_low,
                        'strength': round(buy1['strength'] * 0.8, 2),
                        'ref_1buy_price': buy1['price'],
                        'desc': f"1买后回调不破新低 {pullback_low:.2f}≥{buy1['price']:.2f}",
                        'type': 'buy'
                    })
                    break

    for sell1 in list(sell_points):
        idx1 = None
        for j, bi in enumerate(bis):
            if bi['end_date'] >= sell1['date']:
                idx1 = j; break
        if idx1 is None or idx1 + 2 >= len(bis):
            continue
        for j in range(idx1, min(idx1 + 5, len(bis) - 1)):
            if bis[j]['type'] == 'up' and j + 1 < len(bis) and bis[j+1]['type'] == 'down':
                pullback_high = bis[j]['end_price']
                if pullback_high <= sell1['price'] * 1.03:
                    sell_points.append({
                        'level': 2, 'name': '第二类卖点(2卖)',
                        'date': bis[j]['end_date'], 'price': pullback_high,
                        'strength': round(sell1['strength'] * 0.8, 2),
                        'ref_1sell_price': sell1['price'],
                        'desc': f"1卖后反弹不创新高 {pullback_high:.2f}≤{sell1['price']:.2f}",
                        'type': 'sell'
                    })
                    break

    # === 第三类买卖点 ===
    for z in zhongshu_list:
        if z['end_bi_idx'] + 2 >= len(bis):
            continue
        leave_bi = bis[z['end_bi_idx'] + 1]
        if z['type'] == 'up':
            if leave_bi['type'] != 'down':
                continue
            if z['end_bi_idx'] + 2 < len(bis):
                cb = bis[z['end_bi_idx'] + 2]
                if cb['type'] == 'up' and cb['end_price'] > z['zd']:
                    buy_points.append({
                        'level': 3, 'name': '第三类买点(3买)',
                        'date': cb['end_date'], 'price': cb['end_price'],
                        'strength': 1.5, 'center_idx': z['index'],
                        'desc': f"回调不进入中枢({z['zd']:.2f}) → {cb['end_price']:.2f}>{z['zd']:.2f}",
                        'type': 'buy'
                    })
        else:
            if leave_bi['type'] != 'up':
                continue
            if z['end_bi_idx'] + 2 < len(bis):
                cb = bis[z['end_bi_idx'] + 2]
                if cb['type'] == 'down' and cb['end_price'] < z['zg']:
                    sell_points.append({
                        'level': 3, 'name': '第三类卖点(3卖)',
                        'date': cb['end_date'], 'price': cb['end_price'],
                        'strength': 1.5, 'center_idx': z['index'],
                        'desc': f"反弹不进入中枢({z['zg']:.2f}) → {cb['end_price']:.2f}<{z['zg']:.2f}",
                        'type': 'sell'
                    })

    return {'buy': buy_points, 'sell': sell_points}


# ========== 综合评分 ==========
def calc_comprehensive_score(bis, zhongshu_list, beichi_signals, maidian, resolved_klines):
    """
    综合评分（缠论 + RSI + MACD）满分10分
    - 缠论买点  最高3分
    - RSI      最高2分
    - MACD     最高2分
    - 中枢位置  最高2分
    - 趋势方向  最高1分
    """
    if not resolved_klines or len(resolved_klines) < 20:
        return {'score': 0, 'detail': {}, 'recommendation': '数据不足'}
    closes = [k['close'] for k in resolved_klines]
    latest_close = closes[-1]

    # RSI
    def calc_rsi14(closes):
        if len(closes) < 15:
            return 50
        gains, losses = [], []
        for i in range(1, len(closes)):
            d = closes[i] - closes[i-1]
            gains.append(max(d, 0)); losses.append(max(-d, 0))
        ag = sum(gains[-14:]) / 14
        al = sum(losses[-14:]) / 14
        if al == 0: return 100
        return 100 - (100 / (1 + ag / al))
    rsi = calc_rsi14(closes)

    # MACD
    ema12 = _calc_ema(closes, 12)
    ema26 = _calc_ema(closes, 26)
    dif = ema12[-1] - ema26[-1]
    dif_arr = [ema12[i] - ema26[i] for i in range(len(closes))]
    dea = _calc_ema(dif_arr, 9)[-1]
    macd_hist = 2 * (dif - dea)

    # 趋势
    recent = bis[-4:] if len(bis) >= 4 else bis
    up_cnt = sum(1 for b in recent if b['type'] == 'up')
    down_cnt = len(recent) - up_cnt
    trend = 'up' if up_cnt > down_cnt else ('down' if down_cnt > up_cnt else 'neutral')

    detail = {}
    total = 0.0

    # 1. 缠论买点（3分）
    buys = maidian.get('buy', [])
    if buys:
        # 取最强且最近的买点
        buys_sorted = sorted(buys, key=lambda x: -x['strength'])
        best = buys_sorted[0]
        level_mult = {1: 1.0, 2: 0.7, 3: 0.5}
        chan_score = min(best['strength'] * level_mult.get(best['level'], 0.5), 3.0)
        detail['缠论买点'] = f"{best['name']} 强度{best['strength']}分"
    else:
        chan_score = 0
        detail['缠论买点'] = '无明显买点'
    total += chan_score

    # 2. RSI（2分）
    if rsi < 30:
        rsi_score = 2.0; detail['RSI'] = f"{rsi:.0f} 严重超卖 ✅"
    elif rsi < 40:
        rsi_score = 1.5; detail['RSI'] = f"{rsi:.0f} 偏弱超卖 ✅"
    elif 40 <= rsi <= 60:
        rsi_score = 1.0; detail['RSI'] = f"{rsi:.0f} 中性区间"
    elif 60 < rsi <= 70:
        rsi_score = 0.5; detail['RSI'] = f"{rsi:.0f} 偏强"
    else:
        rsi_score = 0.0; detail['RSI'] = f"{rsi:.0f} 超买 ⚠️"
    total += rsi_score

    # 3. MACD（2分）
    if dif > 0 and macd_hist > 0:
        macd_score = 2.0; detail['MACD'] = '多头状态 ✅'
    elif dif > 0 and -0.5 < macd_hist < 0:
        macd_score = 1.5; detail['MACD'] = '接近金叉 ✅'
    elif dif < 0 and macd_hist < 0:
        macd_score = 0.5; detail['MACD'] = '空头状态 ⚠️'
    else:
        macd_score = 1.0; detail['MACD'] = '整理中'
    total += macd_score

    # 4. 中枢位置（2分）
    if zhongshu_list and resolved_klines:
        latest_z = zhongshu_list[-1]
        if latest_close > latest_z['zg']:
            center_score = 2.0; detail['中枢位置'] = f"价格在{latest_z['zg']:.2f}上方，多头 ✅"
        elif latest_close > latest_z['zd']:
            center_score = 1.0; detail['中枢位置'] = f"价格在中枢内震荡"
        else:
            center_score = 0.0; detail['中枢位置'] = f"价格在{latest_z['zd']:.2f}下方，空头 ⚠️"
    else:
        center_score = 1.0; detail['中枢位置'] = '无中枢信号'
    total += center_score

    # 5. 趋势（1分）
    if trend == 'up':
        trend_score = 1.0; detail['趋势'] = '上升趋势 ✅'
    elif trend == 'down':
        trend_score = 0.0; detail['趋势'] = '下降趋势 ⚠️'
    else:
        trend_score = 0.5; detail['趋势'] = '震荡整理'
    total += trend_score

    # 建议
    score = round(total, 1)
    if score >= 7.5:
        recommendation = '强烈买入'
    elif score >= 6.0:
        recommendation = '建议买入'
    elif score >= 4.5:
        recommendation = '谨慎关注'
    elif score >= 3.0:
        recommendation = '建议观望'
    else:
        recommendation = '建议卖出/空仓'

    return {
        'score': score, 'max': 10.0,
        'detail': detail,
        'recommendation': recommendation,
        'rsi': round(rsi, 1),
        'macd_hist': round(macd_hist, 3),
        'dif': round(dif, 3),
        'trend': trend,
    }


# ========== 可视化 & 展示 ==========
def print_zhongshu(zhongshu_list):
    """打印中枢列表"""
    if not zhongshu_list:
        print("  （未识别到中枢）")
        return
    print(f"\n🏛️  中枢识别结果（共 {len(zhongshu_list)} 个）")
    print(f"{'='*85}")
    print(f"{'编号':<4} {'起始日期':<12} {'结束日期':<12} {'上轨ZG':>8} {'下轨ZD':>8} {'宽度%':>7}")
    print(f"{'-'*85}")
    for z in zhongshu_list:
        print(f"{z['index']:<4} {z['start_date']:<12} {z['end_date']:<12} "
              f"{z['zg']:>8.2f} {z['zd']:>8.2f} {z['range_width']:>6.2f}%")

def print_beichi(beichi_signals):
    """打印背驰信号"""
    if not beichi_signals:
        print("  （未识别到背驰）")
        return
    print(f"\n⚡ 背驰信号（共 {len(beichi_signals)} 个）")
    print(f"{'='*85}")
    print(f"{'类型':<8} {'日期':<12} {'前价格':>8} {'后价格':>8} {'力度比':>7} {'强度':>5} {'中枢#':>5} {'描述'}")
    print(f"{'-'*85}")
    for bc in beichi_signals:
        icon = '🔴顶背驰' if bc['type'] == '顶背驰' else '🟢底背驰'
        print(f"{icon:<10} {bc['date']:<12} {bc['price_before']:>8.2f} {bc['price_after']:>8.2f} "
              f"{bc['bei_ratio']:>7.1f}x {bc['strength']:>5.1f} 中枢{bc['center_idx']:<3} {bc['desc']}")

def print_maidian(maidian):
    """打印买卖点"""
    buys = maidian.get('buy', [])
    sells = maidian.get('sell', [])
    print(f"\n🎯 三类买卖点")
    print(f"{'='*85}")
    if not buys and not sells:
        print("  （未识别到买卖点）")
        return
    if buys:
        print(f"  【买点】")
        for b in buys:
            icon = {1: '🥇', 2: '🥈', 3: '🥉'}.get(b['level'], '•')
            print(f"    {icon} {b['name']} | 日期:{b['date']} | 价格:{b['price']:.2f} | 强度:{b['strength']} | {b['desc']}")
    if sells:
        print(f"  【卖点】")
        for s in sells:
            icon = {1: '🥇', 2: '🥈', 3: '🥉'}.get(s['level'], '•')
            print(f"    {icon} {s['name']} | 日期:{s['date']} | 价格:{s['price']:.2f} | 强度:{s['strength']} | {s['desc']}")

def print_score(score_result):
    """打印综合评分"""
    r = score_result
    if r.get('recommendation') == '数据不足':
        print("\n  （数据不足，无法评分）")
        return
    print(f"\n📊 综合评分: {r['score']:.1f}/10  →  {r['recommendation']}  {'✅' if r['score'] >= 6 else '⚠️' if r['score'] >= 4 else '🔴'}")
    print(f"  {'='*50}")
    for k, v in r.get('detail', {}).items():
        print(f"  {k:<10} {v}")
    print(f"  {'-'*50}")
    print(f"  RSI={r.get('rsi',0):.0f}  MACD柱={r.get('macd_hist',0):.2f}  趋势={r.get('trend','?')}")

def print_bis(bis, resolved_klines=None):
    """打印笔列表（resolved_klines参数已保留但不再使用）"""
    """打印笔列表"""
    if not bis:
        print("  （未识别到笔）")
        return
    up_count = sum(1 for b in bis if b['type'] == 'up')
    down_count = sum(1 for b in bis if b['type'] == 'down')
    print(f"\n📊 笔识别结果（共 {len(bis)} 笔 | ↑上升{up_count}笔 ↓下降{down_count}笔）")
    print(f"{'='*80}")
    print(f"{'类型':<4} {'起始日期':<12} {'结束日期':<12} {'起始价':>8} {'结束价':>8} {'幅度':>7} {'K线数':>5}")
    print(f"{'-'*80}")
    for bi in bis:
        arrow = '↑' if bi['type'] == 'up' else '↓'
        color_tag = '🟢' if bi['type'] == 'up' else '🔴'
        print(f"{color_tag}{arrow:<2} {bi['start_date']:<12} {bi['end_date']:<12} "
              f"{bi['start_price']:>8.2f} {bi['end_price']:>8.2f} {bi['amplitude']:>+6.1f}% {bi['bars_count']:>4d}")


def print_segs(segs):
    """打印线段列表"""
    if not segs:
        print("\n  （未识别到线段，需3个以上同方向笔）")
        return
    print(f"\n📊 线段识别结果（共 {len(segs)} 段）")
    print(f"{'='*80}")
    print(f"{'类型':<4} {'起始日期':<12} {'结束日期':<12} {'起始价':>8} {'结束价':>8} {'幅度':>7} {'笔数':>4}")
    print(f"{'-'*80}")
    for seg in segs:
        arrow = '↑' if seg['type'] == 'up' else '↓'
        color_tag = '🟢' if seg['type'] == 'up' else '🔴'
        print(f"{color_tag}{arrow:<2} {seg['start_date']:<12} {seg['end_date']:<12} "
              f"{seg['start_price']:>8.2f} {seg['end_price']:>8.2f} {seg['amplitude']:>+6.1f}% {seg['bi_count']:>4d}")


def print_klines_comparison(klines, resolved, max_show=40):
    """打印原始K线与处理后K线对比"""
    print(f"\n📋 K线包含处理对比（显示最近{max_show}根）")
    n = min(len(klines), len(resolved), max_show)
    print(f"{'-'*80}")
    print(f"{'日期':<12} {'原始-开':>7} {'原始-高':>7} {'原始-低':>7} {'原始-收':>7} | {'处理-高':>7} {'处理-低':>7}")
    print(f"{'-'*80}")
    for i in range(n):
        k = klines[-(n - i)]
        r = resolved[-(min(n, len(resolved)) - i)] if i < len(resolved) else k
        changed = " *变更*" if (r['high'] != k['high'] or r['low'] != k['low']) else ""
        print(f"{k['date']:<12} {k['open']:>7.2f} {k['high']:>7.2f} {k['low']:>7.2f} {k['close']:>7.2f} | "
              f"{r['high']:>7.2f} {r['low']:>7.2f}{changed}")


def print_statistics(bis, segs):
    """打印统计摘要"""
    if not bis:
        return
    ups = [b for b in bis if b['type'] == 'up']
    downs = [b for b in bis if b['type'] == 'down']
    print(f"\n📈 统计摘要")
    print(f"  笔总数: {len(bis)}（↑{len(ups)}笔 ↓{len(downs)}笔）")
    if ups:
        avg_up = sum(b['amplitude'] for b in ups) / len(ups)
        print(f"  上升笔平均幅度: {avg_up:+.2f}%")
    if downs:
        avg_down = sum(b['amplitude'] for b in downs) / len(downs)
        print(f"  下降笔平均幅度: {avg_down:+.2f}%")
    if segs:
        print(f"  线段总数: {len(segs)}")
        max_up = max((s for s in segs if s['type']=='up'), key=lambda s: s['amplitude'], default=None)
        max_down = max((s for s in segs if s['type']=='down'), key=lambda s: s['amplitude'], default=None)
        if max_up:
            print(f"  最大上升线段: {max_up['amplitude']:+.1f}% ({max_up['start_date']}→{max_up['end_date']})")
        if max_down:
            print(f"  最大下降线段: {max_down['amplitude']:+.1f}% ({max_down['start_date']}→{max_down['end_date']})")


# ========== 主分析函数 ==========
def analyze(symbol, days=120, show_raw=False):
    """完整缠论分析（笔段+中枢+背驰+买卖点+综合评分）"""
    secid = secid_of(symbol)
    print(f"\n{'='*80}")
    print(f"🌀 缠论完整分析  股票代码: {symbol}  分析天数: {days}天")
    print(f"{'='*80}")

    klines = get_kline(secid, days)
    if not klines:
        print("❌ 数据获取失败")
        return None

    print(f"✅ 获取K线 {len(klines)} 根（{klines[0]['date']} → {klines[-1]['date']}）")

    # Step 1: 处理包含关系
    resolved = resolve_inclusion(klines)
    print(f"📐 包含处理后：{len(klines)} → {len(resolved)} 根（去除 {len(klines) - len(resolved)} 组包含关系）")

    if show_raw:
        print_klines_comparison(klines, resolved)

    # Step 2: 分型识别
    fenxings = find_fenxing(resolved)
    tops = [f for f in fenxings if f[1] == 'top']
    bottoms = [f for f in fenxings if f[1] == 'bottom']
    print(f"\n🔺 分型识别：共 {len(fenxings)} 个（△顶分型 {len(tops)} 个 ▽底分型 {len(bottoms)} 个）")

    # Step 3: 笔识别
    bis = identify_bi(klines)
    print_bis(bis, resolved)

    # Step 4: 线段识别
    segs = identify_seg(bis)
    print_segs(segs)

    # Step 5: 中枢识别（核心新增）
    zhongshu_list = find_zhongshu(bis)
    print_zhongshu(zhongshu_list)

    # Step 6: MACD力度计算（基于resolved klines，与bi索引对齐）
    macd_data = calc_macd_for_bis(resolved, bis)

    # Step 7: 背驰判断
    beichi_signals = find_beichi(bis, zhongshu_list, macd_data, resolved)
    print_beichi(beichi_signals)

    # Step 8: 三类买卖点
    maidian = find_maidian(bis, zhongshu_list, beichi_signals, klines=klines)
    print_maidian(maidian)

    # Step 9: 综合评分（基于resolved klines）
    score_result = calc_comprehensive_score(bis, zhongshu_list, beichi_signals, maidian, resolved)
    print_score(score_result)

    # Step 10: 统计
    print_statistics(bis, segs)

    print(f"\n{'='*80}")
    print(f"✅ 缠论完整分析完成 | 笔数:{len(bis)} | 线段:{len(segs)} | 中枢:{len(zhongshu_list)} | 背驰:{len(beichi_signals)}")

    return {
        'klines': klines, 'resolved': resolved,
        'fenxings': fenxings, 'bis': bis, 'segs': segs,
        'zhongshu': zhongshu_list, 'macd_data': macd_data,
        'beichi': beichi_signals, 'maidian': maidian, 'score': score_result,
    }


# ========== 命令行入口 ==========
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    symbol = sys.argv[1]
    days = 120
    show_raw = False
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == '--days' and i + 1 < len(args):
            days = int(args[i + 1]); i += 2
        elif args[i] == '--raw':
            show_raw = True; i += 1
        else:
            i += 1
    result = analyze(symbol, days, show_raw)
    if result:
        print(f"\n{'='*80}")
        print(f"✅ 缠论分析完成 | 笔数:{len(result['bis'])} | 线段:{len(result['segs'])} | "
              f"中枢:{len(result['zhongshu'])} | 背驰:{len(result['beichi'])}")
