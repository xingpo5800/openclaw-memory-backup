# 综合诊断引擎
"""
核心诊断逻辑——给出有说服力的诊断报告
"""
from .indicators import calc_price_position

def run_diagnosis(realtime, klines, indicators, selected_indicators):
    """
    综合所有指标，给出诊断结论
    selected_indicators: 用户选择的指标列表
    """
    if not selected_indicators:
        selected_indicators = ['ma', 'macd', 'rsi', 'kdj', 'boll', 'volume', 'patterns']
    
    ma = indicators.get('ma', {})
    macd_data = indicators.get('macd', {})
    rsi_data = indicators.get('rsi', {})
    kdj_data = indicators.get('kdj', {})
    boll_data = indicators.get('boll', {})
    vol_data = indicators.get('volume', {})
    atr_data = indicators.get('atr', {})
    patterns = indicators.get('patterns', [])
    price_pos = calc_price_position(klines)
    
    price = realtime['price']
    prev = realtime['prev_close']
    chg_pct = realtime['chg_pct']
    high = realtime['high']
    low = realtime['low']
    
    # ===== 计算各维度评分 =====
    scores = {}
    details = []
    
    # D1: 趋势评分 (25分)
    d1 = calc_trend_score(ma, price, klines)
    scores['趋势'] = d1['score']
    details.append(d1['detail'])
    
    # D2: 动量评分 (20分)
    d2 = calc_momentum_score(macd_data, rsi_data, kdj_data)
    scores['动量'] = d2['score']
    details.append(d2['detail'])
    
    # D3: 量价评分 (25分) ——最核心
    d3 = calc_volume_score(vol_data, chg_pct, price_pos)
    scores['量价'] = d3['score']
    details.append(d3['detail'])
    
    # D4: 形态评分 (15分)
    d4 = calc_pattern_score(patterns, price_pos, boll_data)
    scores['形态'] = d4['score']
    details.append(d4['detail'])
    
    # D5: 风险评分 (15分)
    d5 = calc_risk_score(rsi_data, kdj_data, chg_pct, vol_data, price_pos, price, atr_data)
    scores['风险'] = d5['score']
    details.append(d5['detail'])
    
    # ===== 综合评分（归一化） =====
    # 各维度权重: 趋势25 + 动量20 + 量价25 + 形态15 + 风险15 = 100
    weights = {'趋势': 25, '动量': 20, '量价': 25, '形态': 15, '风险': 15}
    total = sum(min(scores.get(k, 50), 100) * weights.get(k, 0) / 100 for k in weights)
    
    # ===== 支撑位 & 压力位 =====
    support_resistance = calc_support_resistance(klines, ma, boll_data, price_pos)
    
    # ===== 进场点建议 =====
    entry_points = calc_entry_points(support_resistance, macd_data, rsi_data, vol_data, klines)
    
    # ===== 操作建议 =====
    if total >= 75:
        signal = "⭐⭐⭐ 强烈买入"
        signal_level = 3
    elif total >= 60:
        signal = "⭐⭐ 买入信号"
        signal_level = 2
    elif total >= 45:
        signal = "⭐ 观望"
        signal_level = 1
    elif total >= 30:
        signal = "⚠️ 卖出信号"
        signal_level = -1
    else:
        signal = "🚨 强烈卖出"
        signal_level = -2
    
    # ===== 修复outlook里的total比较 =====
    # 重新从scores计算用于outlook判断的原始总分
    raw_total = sum(scores.values()) / len(scores) if scores else 50
    
    # ===== 市场推演 =====
    outlook = calc_outlook(raw_total, price_pos, macd_data, rsi_data, patterns)
    
    # ===== 诊断报告（人话） =====
    report = generate_report_text(realtime, scores, total, signal, support_resistance, entry_points, patterns, indicators)
    
    return {
        "total_score": total,
        "signal": signal,
        "signal_level": signal_level,
        "dimension_scores": scores,
        "details": details,
        "support_resistance": support_resistance,
        "entry_points": entry_points,
        "patterns": patterns,
        "outlook": outlook,
        "report": report,
        "price_position": price_pos,
    }

def calc_trend_score(ma, price, klines):
    """趋势评分（0-100）"""
    score = 50
    detail_parts = []
    
    ma5 = ma.get('ma5')
    ma10 = ma.get('ma10')
    ma20 = ma.get('ma20')
    ma60 = ma.get('ma60')
    
    if ma5 and ma10 and ma20:
        if ma5 > ma10 > ma20:
            score = 75
            detail_parts.append("均线多头排列，上升趋势")
        elif ma5 < ma10 < ma20:
            score = 25
            detail_parts.append("均线空头排列，下降趋势")
        else:
            score = 50
            detail_parts.append("均线缠绕，方向不明")
    
    if ma20 and price > ma20:
        score = min(100, score + 10)
        detail_parts.append("价格站稳MA20")
    elif ma20 and price < ma20:
        score = max(0, score - 10)
        detail_parts.append("价格跌破MA20")
    
    if ma60 and price > ma60:
        score = min(100, score + 5)
    elif ma60 and price < ma60:
        score = max(0, score - 5)
    
    # 偏离度
    if ma20:
        deviation = abs(price - ma20) / ma20 * 100
        if deviation > 15:
            score = max(0, score - 10)
            detail_parts.append("价格偏离MA20过大，有回调风险")
    
    score = max(0, min(100, score))
    return {
        'score': round(score, 1),
        'detail': {'score': round(score, 1), 'description': '；'.join(detail_parts) if detail_parts else '趋势不明'}
    }

def calc_momentum_score(macd, rsi, kdj):
    """动量评分（0-100）"""
    score = 50
    detail_parts = []
    
    # MACD
    if macd:
        dif = macd.get('dif', 0)
        dea = macd.get('dea', 0)
        if dif > 0 and dif > dea:
            score += 15
            detail_parts.append("MACD零轴上方金叉，多头动能强劲")
        elif dif > 0:
            score += 10
            detail_parts.append("MACD在零轴上方")
        elif dif < 0 and dif < dea:
            score -= 20
            detail_parts.append("MACD零轴下方死叉，空头主导")
        elif dif < 0:
            score -= 10
            detail_parts.append("MACD在零轴下方")
    
    # RSI（最重要）
    if rsi:
        rsi_val = rsi.get('rsi6', 50)
        if rsi_val < 30:
            score += 25
            detail_parts.append(f"RSI={rsi_val}，深度超卖，反弹概率极大")
        elif rsi_val < 40:
            score += 15
            detail_parts.append(f"RSI={rsi_val}，超卖区域，潜在买点")
        elif rsi_val > 70:
            score -= 20
            detail_parts.append(f"RSI={rsi_val}，超买区域，回调风险大")
        elif rsi_val > 60:
            score += 10
            detail_parts.append(f"RSI={rsi_val}，偏强")
    
    # KDJ
    if kdj:
        k = kdj.get('k', 50)
        if k < 20:
            score += 10
            detail_parts.append(f"KDJ超卖（K={k}）")
        elif k > 80:
            score -= 10
            detail_parts.append(f"KDJ超买（K={k}）")
    
    score = max(0, min(100, score))
    return {
        'score': round(score, 1),
        'detail': {'score': round(score, 1), 'description': '；'.join(detail_parts) if detail_parts else '动量中性'}
    }

def calc_volume_score(vol_data, chg_pct, price_pos):
    """量价评分（0-100）"""
    score = 50
    detail_parts = []
    
    if not vol_data:
        return {'score': 50, 'detail': {'score': 50, 'description': '量能数据不足'}}
    
    vol_ratio = vol_data.get('vol_ratio', 1)
    
    if vol_ratio > 2.0:
        if chg_pct > 2:
            score = 70
            detail_parts.append(f"异常放量上涨（量比{vol_ratio}倍）")
        elif chg_pct < -2:
            score = 30
            detail_parts.append(f"放量下跌（量比{vol_ratio}倍）")
        else:
            score = 50
            detail_parts.append(f"量能异常放大{vol_ratio}倍")
    elif vol_ratio > 1.5:
        if chg_pct > 1:
            score = 75
            detail_parts.append("温和放量上涨，健康")
        elif chg_pct < -1:
            score = 35
            detail_parts.append("放量下跌，需警惕")
        else:
            score = 60
            detail_parts.append("量能温和放大")
    elif vol_ratio < 0.5:
        if chg_pct > 1:
            score = 40
            detail_parts.append("缩量上涨，动能不足")
        elif chg_pct < -1:
            score = 65
            detail_parts.append("缩量下跌，见底信号")
        else:
            score = 50
            detail_parts.append("量能萎缩")
    else:
        if chg_pct > 0:
            score = 60
            detail_parts.append("量价正常")
        else:
            score = 45
            detail_parts.append("量价背离")
    
    # 低位放量加分（核心逻辑）
    if price_pos < 25:
        score = min(100, score + 15)
        detail_parts.append(f"低位区（{price_pos}%）")
    elif price_pos > 75:
        score = max(0, score - 10)
        detail_parts.append(f"高位区（{price_pos}%）")
    
    score = max(0, min(100, score))
    return {
        'score': round(score, 1),
        'detail': {'score': round(score, 1), 'description': '；'.join(detail_parts) if detail_parts else vol_data.get('signal','')}
    }

def calc_pattern_score(patterns, price_pos, boll_data):
    """形态评分（0-100）"""
    score = 50
    detail_parts = []
    
    for p in patterns:
        if '买入' in p.get('signal','') or '底部' in p.get('type',''):
            score += 15
            detail_parts.append(f"{p['name']}（{p.get('type','')}）")
        elif '卖出' in p.get('signal','') or '顶部' in p.get('type',''):
            score -= 15
            detail_parts.append(f"{p['name']}（{p.get('type','')}）")
    
    if boll_data:
        pos = boll_data.get('position','')
        if '突破上轨' in pos:
            score -= 10
            detail_parts.append("突破布林上轨，超买")
        elif '跌破下轨' in pos:
            score += 10
            detail_parts.append("跌破布林下轨，超卖")
    
    score = max(0, min(100, score))
    return {
        'score': round(score, 1),
        'detail': {'score': round(score, 1), 'description': '；'.join(detail_parts) if detail_parts else '无明显形态信号'}
    }

def calc_risk_score(rsi, kdj, chg_pct, vol_data, price_pos, price, atr_data):
    """风险评分"""
    score = 100
    detail_parts = []
    
    # RSI极值
    if rsi:
        rsi_val = rsi.get('rsi6', 50)
        if rsi_val > 85:
            score -= 25
            detail_parts.append("RSI极度超买，风险极高")
        elif rsi_val > 75:
            score -= 15
            detail_parts.append("RSI超买，回调风险较大")
        elif rsi_val < 15:
            score -= 15
            detail_parts.append("RSI极度超卖")
    
    # 日内振幅
    if chg_pct:
        if abs(chg_pct) > 8:
            score -= 20
            detail_parts.append(f"日内振幅过大（{chg_pct}%），波动风险高")
        elif abs(chg_pct) > 5:
            score -= 10
            detail_parts.append(f"日内波动较大（{chg_pct}%）")
    
    # 位置风险
    if price_pos > 85:
        score -= 15
        detail_parts.append("价格接近区间高点，追高风险大")
    elif price_pos < 15:
        score -= 5
        detail_parts.append("价格接近区间低点，潜在机会")
    
    # ATR波动率
    if atr_data and price:
        atr = atr_data.get('atr', 0)
        if atr and price:
            atr_pct = atr / price * 100
            if atr_pct > 5:
                score -= 10
                detail_parts.append(f"波动率偏高（ATR/{price}={atr_pct:.1f}%）")
    
    if not detail_parts:
        detail_parts.append("无明显风险信号")
    
    return {
        'score': round(max(0, score), 1),
        'detail': {'score': round(max(0, score), 1), 'description': '；'.join(detail_parts)}
    }

def calc_support_resistance(klines, ma, boll_data, price_pos):
    """计算支撑位和压力位"""
    price = klines[-1]["close"]
    highs = [k["high"] for k in klines]
    lows = [k["low"] for k in klines]
    
    # 近20日高低价
    recent_highs = sorted(set(highs[-20:]), reverse=True)[:3]
    recent_lows = sorted(set(lows[-20:]))[:3]
    
    result = {
        "levels": [],
        "support_text": "",
        "resistance_text": "",
    }
    
    # 压力位
    if recent_highs:
        r1 = recent_highs[0]
        if r1 > price * 1.01:
            result["levels"].append({"level": "短期压力", "price": r1, "distance": round((r1-price)/price*100, 1)})
        if len(recent_highs) > 1:
            r2 = recent_highs[1]
            if r2 > price * 1.02:
                result["levels"].append({"level": "中期压力", "price": r2, "distance": round((r2-price)/price*100, 1)})
    
    # 布林上轨
    if boll_data:
        upper = boll_data.get('upper')
        if upper and upper > price * 1.01:
            result["levels"].append({"level": "布林上轨", "price": upper, "distance": round((upper-price)/price*100, 1)})
    
    # 整数关口
    round_price = round(price / 5) * 5
    if round_price > price * 1.02:
        result["levels"].append({"level": "整数关口", "price": round_price, "distance": round((round_price-price)/price*100, 1)})
    
    # 支撑位
    if recent_lows:
        s1 = recent_lows[0]
        if s1 < price * 0.99:
            result["levels"].append({"level": "短期支撑", "price": s1, "distance": round((price-s1)/price*100, 1)})
        if len(recent_lows) > 1:
            s2 = recent_lows[1]
            if s2 < price * 0.98:
                result["levels"].append({"level": "中期支撑", "price": s2, "distance": round((price-s2)/price*100, 1)})
    
    # 布林下轨
    if boll_data:
        lower = boll_data.get('lower')
        if lower and lower < price * 0.99:
            result["levels"].append({"level": "布林下轨", "price": lower, "distance": round((price-lower)/price*100, 1)})
    
    # 均线支撑
    for ma_key in ['ma5', 'ma10', 'ma20']:
        if ma.get(ma_key) and ma[ma_key] < price * 0.98:
            result["levels"].append({"level": f"{ma_key.upper()}支撑", "price": ma[ma_key], "distance": round((price-ma[ma_key])/price*100, 1)})
    
    # 按价格排序
    result["levels"].sort(key=lambda x: x["price"], reverse=True)
    
    return result

def calc_entry_points(sr, macd, rsi, vol_data, klines):
    """计算建议进场点"""
    price = klines[-1]["close"]
    atr = 0
    entries = []
    
    # 支撑位附近考虑买入
    supports = [l for l in sr.get("levels", []) if "支撑" in l.get("level", "") or "布林下轨" in l.get("level", "")]
    
    if supports:
        closest = min(supports, key=lambda x: abs(x['price'] - price))
        if closest['price'] < price:
            entries.append({
                "type": "回踩买入",
                "price": closest['price'],
                "condition": f"等价格回踩{closest['level']}（{closest['price']}元）企稳后买入",
                "stop_loss": round(closest['price'] * 0.97, 2),
                "risk_ratio": f"{abs(price - closest['price'])/price*100:.1f}%",
            })
    
    # 放量突破买入
    if macd and macd.get('dif', 0) > macd.get('dea', 0) and macd.get('dif', 0) > 0:
        # 找最近的压力位
        resistances = [l for l in sr.get("levels", []) if "压力" in l.get("level", "")]
        if resistances:
            nearest = min(resistances, key=lambda x: abs(x['price'] - price))
            if nearest['price'] < price * 1.15:  # 15%以内的压力位
                entries.append({
                    "type": "突破买入",
                    "price": nearest['price'],
                    "condition": f"放量突破{nearest['level']}（{nearest['price']}元）时买入",
                    "stop_loss": round(nearest['price'] * 0.97, 2),
                    "risk_ratio": f"{abs(nearest['price'] - price)/price*100:.1f}%",
                })
    
    # RSI超卖反弹
    if rsi and rsi.get('rsi6', 50) < 35:
        entries.append({
            "type": "超卖反弹",
            "price": price,
            "condition": f"RSI已至{rsi.get('rsi6')}超卖区域，可小仓位试探性买入",
            "stop_loss": round(price * 0.97, 2),
            "risk_ratio": "3%",
        })
    
    return entries

def calc_outlook(total, price_pos, macd, rsi, patterns):
    """市场推演"""
    outlooks = []
    
    # 乐观
    if total >= 65 and price_pos < 60:
        outlooks.append({
            "scenario": "乐观",
            "probability": "较高",
            "condition": "若量能持续配合，可能有一波反弹行情",
            "target": f"若突破压力位，第一目标{price_pos + 15}%空间"
        })
    
    # 中性
    outlooks.append({
        "scenario": "中性",
        "probability": "最高",
        "condition": "震荡整理，等待方向选择",
        "target": "建议观望，等待明确信号"
    })
    
    # 悲观
    if total < 45 or price_pos > 80:
        outlooks.append({
            "scenario": "悲观",
            "probability": "注意",
            "condition": "若跌破支撑位，可能进一步下探",
            "target": "严格止损，控制仓位"
        })
    
    return outlooks

def generate_report_text(rt, scores, total, signal, sr, entries, patterns, indicators):
    """生成人话诊断报告"""
    price = rt['price']
    name = rt['name']
    chg_pct = rt['chg_pct']
    ma = indicators.get('ma', {})
    rsi = indicators.get('rsi', {})
    macd = indicators.get('macd', {})
    vol = indicators.get('volume', {})
    
    lines = []
    lines.append(f"【{name}({rt['code']}) 诊断报告】")
    lines.append(f"现价 {price}元 ({chg_pct:+.2f}%)，综合评分 {total:.0f}分，信号：{signal}")
    lines.append("")
    
    # 趋势
    if scores.get('趋势', 50) >= 65:
        ma_state = "多头排列" if scores.get('趋势', 50) >= 75 else "向好"
        price_state = "站稳" if price > (ma.get('ma20') or 0) else "运行在"
        lines.append(f"📈 趋势：偏多。均线系统{ma_state}，价格{price_state}MA20上方。")
    elif scores.get('趋势', 50) <= 35:
        lines.append("📉 趋势：偏空。均线系统空头排列，价格运行在MA20下方，下降趋势中。")
    else:
        lines.append("📊 趋势：中性。均线缠绕，方向不明，等待突破确认。")
    
    # 动量
    if rsi:
        rsi_val = rsi.get('rsi6', 50)
        rsi_state = rsi.get('state', '')
        lines.append(f"⚡ 动量：RSI={rsi_val}，{rsi_state}。")
    if macd:
        macd_state = macd.get('state', '')
        lines.append(f"  MACD {macd_state}。")
    
    # 量价
    if vol:
        lines.append(f"📊 量能：{vol.get('signal', '')}")
    
    # 形态
    if patterns:
        pattern_names = [p['name'] for p in patterns]
        lines.append(f"🎯 形态：出现{'、'.join(pattern_names)}，{' '.join([p.get('signal','') for p in patterns])}")
    
    # 支撑压力
    if sr.get('levels'):
        supports = [f"{l['level']} {l['price']}元" for l in sr['levels'] if '支撑' in l.get('level','') or '布林下轨' in l.get('level','')]
        resists = [f"{l['level']} {l['price']}元" for l in sr['levels'] if '压力' in l.get('level','') or '布林上轨' in l.get('level','')]
        if supports:
            lines.append(f"🔽 支撑位：{'、'.join(supports[:3])}")
        if resists:
            lines.append(f"🔼 压力位：{'、'.join(resists[:3])}")
    
    # 进场点
    if entries:
        for e in entries[:2]:
            lines.append(f"💡 进场参考：{e['condition']}，止损{e['stop_loss']}元（风险约{e['risk_ratio']}）")
    
    return "\n".join(lines)
