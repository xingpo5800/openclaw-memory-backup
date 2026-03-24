#!/usr/local/bin/python3
"""
个股技术诊断系统 v1.0
输入股票代码，输出多维度诊断报告
"""
import sys, json, re, time
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(__file__).parent

# ========== 数据获取 ==========
def get_realtime(code):
    """Tencent实时行情"""
    import subprocess
    if code.startswith(('0', '3')):
        prefix = 'sz'
    else:
        prefix = 'sh'
    url = f"https://qt.gtimg.cn/q={prefix}{code}"
    r = subprocess.run(["curl", "-s", url], capture_output=True)
    text = r.stdout.decode('gbk', errors='replace')
    # 匹配格式: v_sz300830="51~金现代~..."
    m = re.search(r'\"([^\"]+)\"', text)
    if not m:
        return None
    f = m.group(1).split("~")
    if len(f) < 10:
        return None
    return {
        "name": f[1],
        "code": f[2],
        "price": float(f[3]),
        "prev_close": float(f[4]),
        "open": float(f[5]),
        "vol": int(f[6]) if f[6] else 0,
        "high": float(f[33]) if len(f) > 33 and f[33] else 0,
        "low": float(f[34]) if len(f) > 34 and f[34] else 0,
        "date": f[30] if len(f) > 30 else "",
        "time": f[31] if len(f) > 31 else "",
    }

def get_kline(code, days=60):
    """新浪财经日K线"""
    import subprocess, json
    prefix = 'sz' if code.startswith(('0', '3')) else 'sh'
    url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={prefix}{code}&scale=240&ma=no&datalen={days}"
    r = subprocess.run(["curl", "-s", url], capture_output=True)
    try:
        data = json.loads(r.stdout)
        result = []
        for d in data:
            result.append({
                "date": d["day"],
                "open": float(d["open"]),
                "close": float(d["close"]),
                "high": float(d["high"]),
                "low": float(d["low"]),
                "vol": float(d["volume"]),
            })
        return result
    except:
        return []

# ========== 技术指标计算 ==========
def calc_ma(klines, period):
    closes = [k["close"] for k in klines]
    if len(closes) < period:
        return None
    return sum(closes[-period:]) / period

def calc_ema(klines, period):
    closes = [k["close"] for k in klines]
    if len(closes) < period:
        return None
    k = 2 / (period + 1)
    ema = closes[0]
    for c in closes[1:]:
        ema = c * k + ema * (1 - k)
    return ema

def calc_rsi(klines, period=14):
    closes = [k["close"] for k in klines]
    if len(closes) < period + 1:
        return None
    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calc_macd(klines, fast=12, slow=26, signal=9):
    closes = [k["close"] for k in klines]
    if len(closes) < slow:
        return None, None, None
    k_fast = 2 / (fast + 1)
    k_slow = 2 / (slow + 1)
    k_sig = 2 / (signal + 1)
    ema_fast = closes[0]
    ema_slow = closes[0]
    for c in closes[1:]:
        ema_fast = c * k_fast + ema_fast * (1 - k_fast)
        ema_slow = c * k_slow + ema_slow * (1 - k_slow)
    dif = ema_fast - ema_slow
    dea = dif * k_sig  # simplified
    for c in closes[-signal:]:
        dea = dif * k_sig + dea * (1 - k_sig)
    macd_bar = 2 * (dif - dea)
    return dif, dea, macd_bar

def calc_vol_ma(klines, period=5):
    vols = [k["vol"] for k in klines]
    if len(vols) < period:
        return None
    return sum(vols[-period:]) / period

def calc_atr(klines, period=14):
    if len(klines) < period + 1:
        return None
    trs = []
    for i in range(1, len(klines)):
        high = klines[i]["high"]
        low = klines[i]["low"]
        prev_close = klines[i-1]["close"]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
    return sum(trs[-period:]) / period

def detect_kline_pattern(klines):
    """简化K线形态识别"""
    if len(klines) < 3:
        return []
    patterns = []
    c1, c2, c3 = klines[-3], klines[-2], klines[-1]
    
    # 早晨之星
    if (c1["close"] < c1["open"] and  # 第一天阴线
        abs(c2["close"] - c2["open"]) < (c2["high"] - c2["low"]) * 0.3 and  # 第二天十字星
        c3["close"] > c3["open"] and c3["close"] > (c1["open"] + c1["close"]) / 2):  # 第三天阳线
        patterns.append("🌟 早晨之星（底部反转）")
    
    # 黄昏之星
    if (c1["close"] > c1["open"] and
        abs(c2["close"] - c2["open"]) < (c2["high"] - c2["low"]) * 0.3 and
        c3["close"] < c3["open"] and c3["close"] < (c1["open"] + c1["close"]) / 2):
        patterns.append("🌙 黄昏之星（顶部反转）")
    
    # 锤子线
    body = abs(c3["close"] - c3["open"])
    lower_shadow = min(c3["open"], c3["close"]) - c3["low"]
    upper_shadow = c3["high"] - max(c3["open"], c3["close"])
    if lower_shadow > body * 2 and upper_shadow < body * 0.5:
        patterns.append("🔨 锤子线（触底信号）")
    
    # 吞没
    if len(klines) >= 2:
        body1 = abs(c2["close"] - c2["open"])
        body2 = abs(c3["close"] - c3["open"])
        if (c2["close"] < c2["open"] and c3["close"] > c3["open"] and
            c3["close"] > c2["open"] and c3["open"] < c2["close"]):
            patterns.append("📈 阳包阴（多头反攻）")
        if (c2["close"] > c2["open"] and c3["close"] < c3["open"] and
            c3["close"] < c2["open"] and c3["open"] > c2["close"]):
            patterns.append("📉 阴包阳（空头反攻）")
    
    return patterns

# ========== 诊断引擎 ==========
def diagnose(code):
    rt = get_realtime(code)
    kl = get_kline(code, 60)
    
    if not rt:
        return {"error": f"无法获取 {code} 的数据，请检查股票代码"}
    if len(kl) < 20:
        return {"error": f"K线数据不足（{len(kl)}天），无法诊断"}
    
    price = rt["price"]
    prev = rt["prev_close"]
    chg_pct = (price - prev) / prev * 100 if prev else 0
    
    # 计算指标
    ma5 = calc_ma(kl, 5)
    ma10 = calc_ma(kl, 10)
    ma20 = calc_ma(kl, 20)
    ma60 = calc_ma(kl, 60)
    rsi = calc_rsi(kl)
    dif, dea, macd_bar = calc_macd(kl)
    vol_ma5 = calc_vol_ma(kl)
    atr = calc_atr(kl)
    today_vol = kl[-1]["vol"] if kl else 0
    vol_ratio = today_vol / vol_ma5 if vol_ma5 else 0
    
    # ===== D1 趋势诊断 =====
    d1_score = 50
    d1_detail = []
    trend_state = "震荡"
    if ma5 and ma10 and ma20:
        if ma5 > ma10 > ma20:
            d1_score = 85
            trend_state = "多头排列"
            d1_detail.append("均线多头：MA5>MA10>MA20")
        elif ma5 < ma10 < ma20:
            d1_score = 20
            trend_state = "空头排列"
            d1_detail.append("均线空头：MA5<MA10<MA20")
        else:
            d1_score = 50
            trend_state = "震荡整理"
            d1_detail.append("均线缠绕，方向不明")
    if ma20 and price > ma20:
        d1_score = min(100, d1_score + 10)
        d1_detail.append("价格站稳MA20")
    elif ma20 and price < ma20:
        d1_score = max(0, d1_score - 10)
        d1_detail.append("价格跌破MA20")
    if ma60 and price > ma60:
        d1_score = min(100, d1_score + 5)
    elif ma60 and price < ma60:
        d1_score = max(0, d1_score - 5)
    
    # ===== D2 动量诊断 =====
    d2_score = 50
    d2_detail = []
    momentum_state = "中性"
    if rsi:
        if rsi < 30:
            d2_score = 85
            momentum_state = "超卖（潜在买点）"
            d2_detail.append(f"RSI={rsi:.1f}，超卖区域")
        elif rsi < 40:
            d2_score = 70
            momentum_state = "偏弱但未超卖"
            d2_detail.append(f"RSI={rsi:.1f}，接近超卖")
        elif rsi > 70:
            d2_score = 25
            momentum_state = "超买（潜在卖点）"
            d2_detail.append(f"RSI={rsi:.1f}，超买区域")
        elif rsi > 60:
            d2_score = 60
            momentum_state = "偏强"
            d2_detail.append(f"RSI={rsi:.1f}，偏强区域")
        else:
            d2_detail.append(f"RSI={rsi:.1f}，中性区域")
    
    if dif is not None and dea is not None:
        if dif > dea and dif > 0:
            d2_score = min(100, d2_score + 10)
            d2_detail.append("MACD零轴上方金叉")
        elif dif > dea:
            d2_score = min(100, d2_score + 5)
            d2_detail.append("MACD金叉，零轴下方")
        elif dif < dea:
            d2_score = max(0, d2_score - 10)
            d2_detail.append("MACD死叉")
    
    # ===== D3 量价诊断（最核心） =====
    d3_score = 50
    d3_detail = []
    volume_signal = "中性"
    
    # 量能分析
    if vol_ratio > 2.0:
        d3_score = 30 if chg_pct < 0 else 80
        volume_signal = "异常放量" + ("（疑似出货）" if chg_pct < 0 else "（主力进场？）")
        d3_detail.append(f"量能放大{vol_ratio:.1f}倍")
    elif vol_ratio > 1.5:
        if chg_pct > 1:
            d3_score = 85
            volume_signal = "放量上涨（健康）"
            d3_detail.append(f"量增价涨，量比{vol_ratio:.1f}x")
        elif chg_pct < -1:
            d3_score = 25
            volume_signal = "放量下跌（危险）"
            d3_detail.append(f"量增价跌，量比{vol_ratio:.1f}x")
        else:
            d3_score = 60
            volume_signal = "温和放量"
            d3_detail.append(f"量比{vol_ratio:.1f}x")
    elif vol_ratio < 0.5:
        if chg_pct > 1:
            d3_score = 40
            volume_signal = "缩量上涨（警惕）"
            d3_detail.append("量能萎缩，上涨乏力")
        elif chg_pct < -1:
            d3_score = 70
            volume_signal = "缩量下跌（可能见底）"
            d3_detail.append("缩量下跌，卖压减轻")
        else:
            d3_score = 50
            d3_detail.append("量能低迷")
    else:
        if chg_pct > 0:
            d3_score = 65
            volume_signal = "量价配合"
            d3_detail.append("量能温和，价格上涨")
        else:
            d3_score = 45
            volume_signal = "量价背离"
            d3_detail.append("价格下跌，量能收缩")
    
    # 关键：低位判断（毅哥教导）
    low_point = min(k["low"] for k in kl[-20:]) if len(kl) >= 20 else kl[0]["low"]
    high_point = max(k["high"] for k in kl[-20:]) if len(kl) >= 20 else kl[-1]["high"]
    price_pos = (price - low_point) / (high_point - low_point) * 100 if high_point > low_point else 50
    
    if price_pos < 30:
        d3_score = min(100, d3_score + 15)
        d3_detail.append(f"价格处于低位区间({price_pos:.0f}%)，低位放量=进场信号")
    elif price_pos > 70:
        d3_score = max(0, d3_score - 15)
        d3_detail.append(f"价格处于高位区间({price_pos:.0f}%)，高位放量=警惕")
    
    # ===== D4 形态诊断 =====
    d4_score = 50
    d4_detail = []
    patterns = detect_kline_pattern(kl)
    for p in patterns:
        d4_detail.append(p)
        if "底" in p or "多头" in p or "锤子" in p:
            d4_score = min(100, d4_score + 20)
        elif "顶" in p or "空头" in p:
            d4_score = max(0, d4_score - 20)
    
    # 支撑阻力
    recent_highs = sorted([k["high"] for k in kl[-20:]], reverse=True)[:3]
    recent_lows = sorted([k["low"] for k in kl[-20:]])[:3]
    if recent_lows:
        d4_detail.append(f"近期支撑：{recent_lows[0]:.2f}元")
    if recent_highs:
        d4_detail.append(f"近期阻力：{recent_highs[0]:.2f}元")
    
    # ===== D5 相对强弱 =====
    d5_score = 50 + (chg_pct - 0) * 5  # 简单对比大盘
    d5_score = max(0, min(100, d5_score))
    d5_detail = [f"今日涨跌: {chg_pct:+.2f}%"]
    
    # ===== D6 风险诊断 =====
    d6_score = 100
    d6_detail = []
    if rsi and (rsi > 85 or rsi < 15):
        d6_score -= 30
        d6_detail.append("RSI极值，风险偏高")
    if atr and price:
        daily_range = (rt["high"] - rt["low"]) / price * 100 if rt["high"] > rt["low"] else 0
        if daily_range > 8:
            d6_score -= 20
            d6_detail.append(f"日内振幅{daily_range:.1f}%，波动较大")
    if price_pos > 85:
        d6_score -= 15
        d6_detail.append("价格接近区间高点，追高风险大")
    if price_pos < 15:
        d6_score -= 5
        d6_detail.append("价格接近区间低点，潜在反弹机会")
    if not d6_detail:
        d6_detail.append("无明显风险信号")
    
    # ===== 综合评分 =====
    total = (d1_score * 0.25 + d2_score * 0.20 + d3_score * 0.25 +
             d4_score * 0.15 + d5_score * 0.10 + d6_score * 0.05)
    
    if total >= 80:
        signal = "⭐⭐⭐ 强烈买入"
    elif total >= 65:
        signal = "⭐⭐ 买入信号"
    elif total >= 45:
        signal = "⭐ 观望"
    elif total >= 30:
        signal = "⚠️ 卖出信号"
    else:
        signal = "🚨 强烈卖出"
    
    return {
        "name": rt["name"],
        "code": code,
        "time": f"{rt['date']} {rt['time']}",
        "price": price,
        "chg_pct": chg_pct,
        "total_score": round(total, 1),
        "signal": signal,
        "dimensions": {
            "D1_趋势": {"score": round(d1_score, 1), "state": trend_state, "detail": d1_detail},
            "D2_动量": {"score": round(d2_score, 1), "state": momentum_state, "detail": d2_detail},
            "D3_量价": {"score": round(d3_score, 1), "state": volume_signal, "detail": d3_detail},
            "D4_形态": {"score": round(d4_score, 1), "state": "", "detail": d4_detail},
            "D5_强弱": {"score": round(d5_score, 1), "state": "", "detail": d5_detail},
            "D6_风险": {"score": round(d6_score, 1), "state": "", "detail": d6_detail},
        },
        "key_data": {
            "MA5": round(ma5, 2) if ma5 else None,
            "MA10": round(ma10, 2) if ma10 else None,
            "MA20": round(ma20, 2) if ma20 else None,
            "MA60": round(ma60, 2) if ma60 else None,
            "RSI": round(rsi, 1) if rsi else None,
            "MACD_DIF": round(dif, 3) if dif else None,
            "MACD_DEA": round(dea, 3) if dea else None,
            "MACD_BAR": round(macd_bar, 3) if macd_bar else None,
            "VOL_RATIO": round(vol_ratio, 2) if vol_ratio else None,
            "ATR": round(atr, 2) if atr else None,
            "今日量能": round(today_vol, 0) if today_vol else None,
            "5日均量": round(vol_ma5, 0) if vol_ma5 else None,
            "低位区间": f"{price_pos:.0f}%" if price_pos else None,
        }
    }

# ========== 报告生成 ==========
def print_report(result):
    if "error" in result:
        print(f"❌ {result['error']}")
        return
    
    print()
    print("━" * 55)
    print(f"  📋 个股技术诊断报告  |  {result['time']}")
    print("━" * 55)
    print(f"  🎯 {result['name']}({result['code']})  现价:{result['price']}  {result['chg_pct']:+.2f}%")
    print()
    print(f"  ╔══════════════════════════════════════╗")
    print(f"  ║  🎯 综合评分：{result['total_score']:>5.1f} / 100        ║")
    print(f"  ║  📊 操作信号：{result['signal']:<18s}║")
    print(f"  ╚══════════════════════════════════════╝")
    print()
    
    print(f"  {'维度':<8} {'评分':>6}  {'状态/详情'}")
    print(f"  {'─'*55}")
    for dim, data in result["dimensions"].items():
        bar = "█" * int(data["score"] / 10) + "░" * (10 - int(data["score"] / 10))
        print(f"  {dim:<8} {data['score']:>5.1f}  {bar} {data.get('state','')}")
        for d in data.get("detail", []):
            print(f"  {'':8} {'':>6}    • {d}")
    print()
    print(f"  【关键指标】")
    print(f"  {'─'*55}")
    kd = result["key_data"]
    print(f"  MA5={kd.get('MA5')} MA10={kd.get('MA10')} MA20={kd.get('MA20')} MA60={kd.get('MA60')}")
    print(f"  RSI={kd.get('RSI')}  MACD DIF={kd.get('MACD_DIF')}  DEA={kd.get('MACD_DEA')}")
    print(f"  量比={kd.get('VOL_RATIO')}x  ATR={kd.get('ATR')}  {kd.get('低位区间','')}")
    print()
    print(f"  ⚠️  仅为技术分析，不构成投资建议。")
    print("━" * 55)

# ========== 主程序 ==========
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 diagnose.py <股票代码>")
        print("例如: python3 diagnose.py 300830")
        sys.exit(1)
    
    code = sys.argv[1].zfill(6)
    result = diagnose(code)
    print_report(result)
