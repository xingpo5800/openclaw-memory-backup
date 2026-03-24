# 技术指标计算引擎
"""
计算所有技术指标，返回字典供诊断使用
"""
import json

def calc_all_indicators(klines):
    """计算所有指标"""
    if len(klines) < 5:
        return {}
    
    closes = [k["close"] for k in klines]
    highs = [k["high"] for k in klines]
    lows = [k["low"] for k in klines]
    vols = [k["vol"] for k in klines]
    
    return {
        "ma": calc_ma_all(klines),
        "ema": calc_ema_all(klines),
        "macd": calc_macd(klines),
        "rsi": calc_rsi(klines),
        "kdj": calc_kdj(klines),
        "boll": calc_boll(klines),
        "volume": calc_volume_analysis(klines),
        "atr": calc_atr(klines),
        "patterns": detect_patterns(klines),
        "price_position": calc_price_position(klines),
    }

def calc_ma_all(klines, periods=[5, 10, 20, 30, 60]):
    """计算所有均线"""
    closes = [k["close"] for k in klines]
    result = {}
    for p in periods:
        if len(closes) >= p:
            ma = sum(closes[-p:]) / p
            result[f"ma{p}"] = round(ma, 3)
    return result

def calc_ema_all(klines, periods=[12, 26]):
    """计算EMA"""
    closes = [k["close"] for k in klines]
    result = {}
    for p in periods:
        if len(closes) >= p:
            k = 2 / (p + 1)
            ema = closes[0]
            for c in closes[1:]:
                ema = c * k + ema * (1 - k)
            result[f"ema{p}"] = round(ema, 3)
    return result

def calc_macd(klines, fast=12, slow=26, signal=9):
    """MACD计算"""
    closes = [k["close"] for k in klines]
    if len(closes) < slow + signal:
        return {}
    
    # 计算EMA
    def ema(data, period):
        k = 2 / (period + 1)
        e = data[0]
        for c in data[1:]:
            e = c * k + e * (1 - k)
        return e
    
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    dif = ema_fast - ema_slow
    
    # DEA用简单平均近似
    dea = dif * 0.9  # 简化
    
    macd_bar = 2 * (dif - dea)
    
    # 判断状态
    if dif > 0 and dif > dea:
        state = "多头（金叉）"
    elif dif < 0 and dif < dea:
        state = "空头（死叉）"
    elif dif > dea:
        state = "反弹中"
    else:
        state = "整理中"
    
    return {
        "dif": round(dif, 4),
        "dea": round(dea, 4),
        "macd_bar": round(macd_bar, 4),
        "state": state,
    }

def calc_rsi(klines, period=14):
    """RSI计算"""
    closes = [k["close"] for k in klines]
    if len(closes) < period + 1:
        return {}
    
    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        rsi = 100
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
    
    # 判断状态
    if rsi < 30:
        state = "超卖（潜在买点）"
    elif rsi < 40:
        state = "偏弱"
    elif rsi > 70:
        state = "超买（潜在卖点）"
    elif rsi > 60:
        state = "偏强"
    else:
        state = "中性"
    
    return {
        "rsi6": round(rsi, 1),
        "state": state,
    }

def calc_kdj(klines, period=9):
    """KDJ计算"""
    highs = [k["high"] for k in klines]
    lows = [k["low"] for k in klines]
    closes = [k["close"] for k in klines]
    
    if len(klines) < period:
        return {}
    
    # 最近9日
    recent_highs = highs[-period:]
    recent_lows = lows[-period:]
    recent_closes = closes[-period:]
    
    highest_high = max(recent_highs)
    lowest_low = min(recent_lows)
    
    rsv = (recent_closes[-1] - lowest_low) / (highest_high - lowest_low) * 100 if highest_high > lowest_low else 50
    
    k = 50
    d = 50
    for _ in range(3):  # 平滑
        k = 2/3 * k + 1/3 * rsv
        d = 2/3 * d + 1/3 * k
    
    j = 3 * k - 2 * d
    
    if k < 20 and d < 20:
        state = "超卖区域"
    elif k > 80 and d > 80:
        state = "超买区域"
    elif k > d:
        state = "多方主导"
    else:
        state = "空方主导"
    
    return {
        "k": round(k, 1),
        "d": round(d, 1),
        "j": round(j, 1),
        "state": state,
    }

def calc_boll(klines, period=20, std_dev=2):
    """布林带计算"""
    closes = [k["close"] for k in klines]
    if len(closes) < period:
        return {}
    
    ma = sum(closes[-period:]) / period
    variance = sum((c - ma) ** 2 for c in closes[-period:]) / period
    std = variance ** 0.5
    
    upper = ma + std_dev * std
    lower = ma - std_dev * std
    width = (upper - lower) / ma * 100
    
    current = closes[-1]
    if current > upper:
        position = "突破上轨"
    elif current < lower:
        position = "跌破下轨"
    elif current > ma:
        position = "中轨上方"
    else:
        position = "中轨下方"
    
    return {
        "upper": round(upper, 3),
        "middle": round(ma, 3),
        "lower": round(lower, 3),
        "width": round(width, 2),
        "position": position,
    }

def calc_volume_analysis(klines, period=5):
    """量能分析"""
    vols = [k["vol"] for k in klines]
    closes = [k["close"] for k in klines]
    
    if len(vols) < period + 1:
        return {}
    
    vol_ma = sum(vols[-period:]) / period
    today_vol = vols[-1]
    vol_ratio = today_vol / vol_ma if vol_ma > 0 else 1
    
    # 今日涨跌
    chg = (closes[-1] - closes[-2]) / closes[-2] * 100 if closes[-2] > 0 else 0
    
    if vol_ratio > 2.0:
        if chg > 0:
            signal = "异常放量上涨（警惕）"
        else:
            signal = "放量下跌（恐慌抛售）"
    elif vol_ratio > 1.5:
        if chg > 0:
            signal = "温和放量上涨（健康）"
        else:
            signal = "放量下跌（出货嫌疑）"
    elif vol_ratio < 0.5:
        if chg > 0:
            signal = "缩量上涨（不可持续）"
        else:
            signal = "缩量下跌（见底信号？）"
    else:
        if chg > 0:
            signal = "量价配合正常"
        else:
            signal = "量价背离"
    
    return {
        "vol_ma": round(vol_ma, 0),
        "vol_ratio": round(vol_ratio, 2),
        "chg_pct": round(chg, 2),
        "signal": signal,
    }

def calc_atr(klines, period=14):
    """ATR真实波幅"""
    if len(klines) < period + 1:
        return {}
    
    trs = []
    for i in range(1, len(klines)):
        high = klines[i]["high"]
        low = klines[i]["low"]
        prev_close = klines[i-1]["close"]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
    
    atr = sum(trs[-period:]) / period
    return {"atr": round(atr, 3)}

def detect_patterns(klines):
    """K线形态识别"""
    if len(klines) < 3:
        return []
    
    patterns = []
    c1, c2, c3 = klines[-3], klines[-2], klines[-1]
    
    def body(k): return abs(k["close"] - k["open"])
    def upper_shadow(k): return k["high"] - max(k["open"], k["close"])
    def lower_shadow(k): return min(k["open"], k["close"]) - k["low"]
    def is_bear(k): return k["close"] < k["open"]
    def is_bull(k): return k["close"] > k["open"]
    
    # 早晨之星
    if (is_bear(c1) and body(c1) > body(c2) * 1.5 and
        body(c2) < (c2["high"] - c2["low"]) * 0.3 and
        is_bull(c3) and c3["close"] > (c1["open"] + c1["close"]) / 2):
        patterns.append({"name": "早晨之星", "type": "底部反转", "signal": "买入信号", "confidence": "高"})
    
    # 黄昏之星
    if (is_bull(c1) and body(c1) > body(c2) * 1.5 and
        body(c2) < (c2["high"] - c2["low"]) * 0.3 and
        is_bear(c3) and c3["close"] < (c1["open"] + c1["close"]) / 2):
        patterns.append({"name": "黄昏之星", "type": "顶部反转", "signal": "卖出信号", "confidence": "高"})
    
    # 锤子线
    b = body(c3)
    ls = lower_shadow(c3)
    us = upper_shadow(c3)
    if ls > b * 2.5 and us < b * 0.3 and c3["close"] > c3["open"]:
        patterns.append({"name": "锤子线", "type": "触底回升", "signal": "买入信号", "confidence": "中"})
    
    # 吞没形态
    if (len(klines) >= 2 and
        is_bear(c2) and is_bull(c3) and
        c3["close"] > c2["open"] and c3["open"] < c2["close"]):
        patterns.append({"name": "阳包阴", "type": "多头反攻", "signal": "买入信号", "confidence": "中"})
    if (len(klines) >= 2 and
        is_bull(c2) and is_bear(c3) and
        c3["close"] < c2["open"] and c3["open"] > c2["close"]):
        patterns.append({"name": "阴包阳", "type": "空头反攻", "signal": "卖出信号", "confidence": "中"})
    
    # 上吊线（顶部）
    if ls > b * 2 and us < b * 0.5 and c3["close"] < c3["open"]:
        patterns.append({"name": "上吊线", "type": "顶部预警", "signal": "谨慎", "confidence": "中"})
    
    # 缺口
    if len(klines) >= 2 and c2["high"] < c1["low"]:
        patterns.append({"name": "向上跳空缺口", "type": "突破缺口", "signal": "强势", "confidence": "中"})
    elif len(klines) >= 2 and c2["low"] > c1["high"]:
        patterns.append({"name": "向下跳空缺口", "type": "突破缺口", "signal": "弱势", "confidence": "中"})
    
    return patterns

def calc_price_position(klines, lookback=60):
    """价格在近期区间的位置"""
    if len(klines) < 5:
        return 50
    
    recent = klines[-lookback:] if len(klines) >= lookback else klines
    highs = [k["high"] for k in recent]
    lows = [k["low"] for k in recent]
    current = klines[-1]["close"]
    
    high = max(highs)
    low = min(lows)
    
    if high == low:
        return 50
    
    pos = (current - low) / (high - low) * 100
    return round(pos, 1)
