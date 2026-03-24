# 数据获取引擎
import subprocess, json, re
from pathlib import Path

def get_realtime(code):
    """Tencent实时行情"""
    prefix = 'sz' if code.startswith(('0', '3')) else 'sh'
    url = f'https://qt.gtimg.cn/q={prefix}{code}'
    r = subprocess.run(["curl", "-s", url], capture_output=True)
    text = r.stdout.decode('gbk', errors='replace')
    m = re.search(r'"([^"]+)"', text)
    if not m:
        return None
    f = m.group(1).split("~")
    if len(f) < 40:
        return None
    
    try:
        pe = f[39] if f[39] and f[39] != '-' else None
        pb = f[46] if len(f) > 46 and f[46] and f[46] != '-' else None
        vol = f[6] if f[6] else '0'
        turnover = f[37] if len(f) > 37 and f[37] and f[37] != '-' else None
        market_cap = f[44] if len(f) > 44 and f[44] and f[44] != '-' else None
        
        return {
            "name": f[1],
            "code": code,
            "price": float(f[3]) if f[3] else 0,
            "prev_close": float(f[4]) if f[4] else 0,
            "open": float(f[5]) if f[5] else 0,
            "vol": int(vol),
            "high": float(f[33]) if len(f) > 33 and f[33] else 0,
            "low": float(f[34]) if len(f) > 34 and f[34] else 0,
            "date": f[30] if len(f) > 30 else '',
            "time": f[31] if len(f) > 31 else '',
            "chg_pct": float(f[32]) if len(f) > 32 and f[32] else 0,
            "pe": float(pe) if pe else None,
            "pb": float(pb) if pb else None,
            "turnover": float(turnover) if turnover else None,
            "market_cap": market_cap,
        }
    except:
        return None

def get_kline(code, days=120):
    """Sina Finance K线"""
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

def get_realtime_batch(codes):
    """批量获取实时行情"""
    results = []
    for code in codes:
        rt = get_realtime(code.strip().zfill(6))
        if rt:
            results.append(rt)
    return results
