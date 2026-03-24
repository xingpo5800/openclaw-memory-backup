#!/usr/local/bin/python3
"""
A股量化交易系统 v1.0
核心理念：短线复利 + 严格止损 + 本金至上

策略逻辑：
1. 选股：强势股回调买入，或突破买入
2. 持仓：3-5个交易日，不短线拖成中线
3. 止损：亏损3%无条件止损（保本第一）
4. 止盈：盈利5%以上分批卖，不坐电梯
5. 空仓：看不懂就等，宁可错过不可做错
"""

import requests
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path(__file__).parent
DATA_DIR = WORKSPACE / "data"
CONFIG_FILE = WORKSPACE / "portfolio.json"
SIGNALS_FILE = WORKSPACE / "signals.json"
BACKTEST_FILE = WORKSPACE / "backtest.json"
DATA_DIR.mkdir(exist_ok=True)

# ========== 数据获取 ==========
def get_realtime_batch(secids):
    """批量实时行情"""
    url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
    params = {
        'secids': secids,
        'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
        'fields': 'f2,f3,f4,f5,f6,f12,f14,f15,f16,f17,f18',
    }
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://quote.eastmoney.com/'}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        return r.json().get('data', {}).get('diff', [])
    except:
        return []

def get_kline(secid, days=250):
    """获取日K线"""
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        'secid': secid, 'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
        'fields1': 'f1,f2,f3,f4,f5,f6',
        'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
        'klt': '101', 'fqt': '1', 'end': '20500101', 'lmt': str(days)
    }
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://quote.eastmoney.com/'}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        raw = r.json().get('data', {}).get('klines', [])
        result = []
        for line in raw:
            p = line.split(',')
            if len(p) >= 6:
                result.append({
                    'date': p[0], 'open': float(p[1]), 'close': float(p[2]),
                    'high': float(p[3]), 'low': float(p[4]), 'volume': int(p[5])
                })
        return result
    except:
        return []

def get_zt_pool(date_str):
    """获取涨停股池（寻找强势股）"""
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        'cb': 'jQuery', 'pn': '1', 'pz': '50', 'po': '1', 'np': '1',
        'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
        'fltt': '2', 'invt': '2', 'fid': 'f3',
        'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048',
        'fields': 'f1,f2,f3,f4,f5,f6,f7,f12,f14,f15,f16,f17,f18',
    }
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://quote.eastmoney.com/zt/'}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        text = r.text
        # 简单解析
        data = []
        import re
        matches = re.findall(r'f12:"(\d+)",f14:"([^"]+)",f2:(\d+),f3:([-\d.]+)', text)
        for m in matches:
            data.append({'code': m[0], 'name': m[1], 'price': int(m[2])/100, 'chg_pct': float(m[3])})
        return data
    except:
        return []

# ========== 技术指标计算 ==========
def calc_ma(closes, n):
    if len(closes) < n:
        return None
    return sum(closes[-n:]) / n

def calc_ema(closes, n):
    k = 2 / (n + 1)
    ema_val = closes[0]
    for d in closes[1:]:
        ema_val = d * k + ema_val * (1 - k)
    return ema_val

def calc_rsi(closes, n=14):
    if len(closes) < n + 1:
        return None
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [d for d in deltas[-n:] if d > 0]
    losses = [-d for d in deltas[-n:] if d < 0]
    avg_gain = sum(gains) / n if gains else 0
    avg_loss = sum(losses) / n if losses else 0
    if avg_loss == 0:
        return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def calc_vol_ratio(volumes, n=5):
    if len(volumes) < n:
        return 1.0
    vol_ma = sum(volumes[-n:]) / n
    return volumes[-1] / vol_ma if vol_ma else 1.0

# ========== 信号生成 ==========
def gen_signal(klines):
    """
    缠论信号策略 v2（2026-03-23优化）
    核心：RSI超卖 + MACD确认
    
    买入：RSI<40超卖区域 + MACD接近金叉（绿柱缩短）
    卖出：RSI>65超买 或 止损3% 或 止盈8% 或 超时5天
    """
    if not klines or len(klines) < 30:
        return 'HOLD', '数据不足'
    
    closes = [k['close'] for k in klines]
    volumes = [k['volume'] for k in klines]
    
    ma5 = calc_ma(closes, 5)
    ma20 = calc_ma(closes, 20)
    rsi = calc_rsi(closes)
    vol_r = calc_vol_ratio(volumes)
    
    # MACD
    def ema(d, n):
        k = 2/(n+1); e = d[0]
        for v in d[1:]: e = v*k + e*(1-k)
        return e
    if len(closes) >= 26:
        e12 = ema(closes, 12)
        e26 = ema(closes, 26)
        macd = e12 - e26
        macds = [ema(closes[:i+1],12)-ema(closes[:i+1],26) for i in range(25,len(closes))]
        signal = sum(macds[-9:])/9
        macd_hist = macd - signal
    else:
        macd_hist = 0
    
    latest = closes[-1]
    
    buy_score = 0
    buy_reasons = []
    
    # 1. RSI超卖（缠论：跌不动了）
    if rsi and rsi < 40:
        buy_score += 3
        buy_reasons.append(f"RSI={rsi:.0f}超卖")
    
    # 2. MACD绿柱缩短（接近金叉确认）
    if macd_hist and -1 < macd_hist < 0.5:
        buy_score += 2
        buy_reasons.append(f"MACD={macd_hist:.2f}近金叉")
    
    # 3. 缩量回调（不破重要支撑）
    if vol_r < 0.9 and ma20 and latest > ma20 * 0.97:
        buy_score += 1
        buy_reasons.append("缩量回调支撑位")
    
    # 4. 大跌后反弹确认
    chg_5d = (closes[-1] - closes[-6]) / closes[-6] * 100 if len(closes) >= 6 else 0
    if chg_5d < -5 and rsi and rsi < 50:
        buy_score += 1
        buy_reasons.append(f"大跌{chg_5d:.0f}%反弹")
    
    sell_score = 0
    sell_reasons = []
    
    # 1. RSI超买
    if rsi and rsi > 65:
        sell_score += 2
        sell_reasons.append(f"RSI={rsi:.0f}超买")
    
    # 2. MACD死叉
    if macd_hist and macd_hist < -0.5:
        sell_score += 1
        sell_reasons.append("MACD死叉")
    
    # 3. 跌破MA20
    if ma20 and latest < ma20:
        sell_score += 1
        sell_reasons.append("跌破MA20")
    
    if buy_score >= 3:
        return 'BUY', f"买入({buy_score}分): {', '.join(buy_reasons)}"
    elif sell_score >= 2:
        return 'SELL', f"卖出({sell_score}分): {', '.join(sell_reasons)}"
    elif buy_score >= 1 and sell_score == 0:
        return 'WATCH', f"关注({buy_score}分): {', '.join(buy_reasons)}"
    else:
        _macd_str = f"{macd_hist:.2f}" if macd_hist else "0"
        return 'HOLD', f"观望 RSI={rsi:.0f} MACD={_macd_str}"

# ========== 选股扫描 ==========
def scan_stocks(symbols):
    """扫描股票池，生成信号"""
    # 获取实时行情
    secids = []
    for s in symbols:
        if s.startswith('6'):
            secids.append(f"1.{s}")
        else:
            secids.append(f"0.{s}")
    
    rt_data = {str(d['f12']): {'price': d['f2']/100, 'chg': d['f3']/100, 'prev': d['f18']/100} 
               for d in get_realtime_batch(','.join(secids))}
    
    results = []
    for sym in symbols:
        secid = f"1.{sym}" if sym.startswith('6') else f"0.{sym}"
        klines = get_kline(secid, 60)
        if not klines:
            continue
        
        rt = rt_data.get(sym, {})
        signal, reason = gen_signal(klines)
        
        closes = [k['close'] for k in klines]
        rsi = calc_rsi(closes)
        vol_r = calc_vol_ratio([k['volume'] for k in klines])
        ma5 = calc_ma(closes, 5)
        ma20 = calc_ma(closes, 20)
        
        chg_today = 0
        if rt.get('price') and rt.get('prev'):
            chg_today = (rt['price'] - rt['prev']) / rt['prev'] * 100
        
        results.append({
            'symbol': sym,
            'name': rt.get('name', sym),
            'price': rt.get('price', closes[-1]),
            'chg_today': chg_today,
            'signal': signal,
            'reason': reason,
            'rsi': rsi or 0,
            'vol_r': vol_r,
            'ma5': ma5 or 0,
            'ma20': ma20 or 0,
        })
        
        # 限速
        time.sleep(0.2)
    
    return results

# ========== 回测引擎 ==========
def backtest(symbol, start_date='2025-01-01', initial_capital=100000):
    """
    缠论信号回测 v2
    规则：
    - 买入信号 → 买入
    - 止损3% → 卖出
    - 止盈8% → 卖出
    - 持仓超5天 → 强制平仓
    """
    secid = f"1.{symbol}" if symbol.startswith('6') else f"0.{symbol}"
    klines = get_kline(secid, 500)
    if not klines:
        return None
    
    # 过滤日期
    klines = [k for k in klines if k['date'] >= start_date]
    if len(klines) < 30:
        return None
    
    capital = initial_capital
    position = 0  # 持股数量
    entry_price = 0
    entry_date = None
    trades = []
    
    for i in range(20, len(klines)):
        window = klines[:i]
        signal, reason = gen_signal(window)
        price = klines[i]['close']
        date = klines[i]['date']
        
        # 持仓中
        if position > 0:
            pnl_pct = (price - entry_price) / entry_price * 100
            days_held = (datetime.strptime(date, '%Y-%m-%d') - datetime.strptime(entry_date, '%Y-%m-%d')).days
            
            sell = False
            sell_reason = ""
            
            # 止损
            if pnl_pct <= -3:
                sell = True
                sell_reason = f"止损({pnl_pct:.1f}%)"
            # 止盈
            elif pnl_pct >= 8:
                sell = True
                sell_reason = f"止盈({pnl_pct:.1f}%)"
            # 超时
            elif days_held >= 5:
                sell = True
                sell_reason = f"超时({days_held}天,{pnl_pct:.1f}%)"
            
            if sell:
                proceeds = position * price
                commission = proceeds * 0.0003  # 万三佣金
                capital = proceeds - commission
                trades.append({
                    'date': date, 'symbol': symbol,
                    'action': 'SELL', 'price': price,
                    'shares': position, 'pnl_pct': pnl_pct,
                    'reason': sell_reason,
                    'capital': capital
                })
                position = 0
                entry_price = 0
                entry_date = None
        
        # 买入
        if signal == 'BUY' and position == 0 and capital >= price * 100:
            shares = int(capital / price / 100) * 100  # 按手买
            cost = shares * price
            commission = cost * 0.0003
            if cost + commission <= capital:
                position = shares
                entry_price = price
                entry_date = date
                capital -= (cost + commission)
                trades.append({
                    'date': date, 'symbol': symbol,
                    'action': 'BUY', 'price': price,
                    'shares': shares, 'reason': reason,
                    'capital': capital
                })
    
    # 计算统计
    if not trades:
        return {'symbol': symbol, 'trades': [], 'total_return': 0, 'win_rate': 0}
    
    sell_trades = [t for t in trades if t['action'] == 'SELL']
    wins = [t for t in sell_trades if t['pnl_pct'] > 0]
    
    final_capital = capital
    if position > 0:
        final_capital += position * klines[-1]['close']
    
    total_return = (final_capital - initial_capital) / initial_capital * 100
    win_rate = len(wins) / len(sell_trades) * 100 if sell_trades else 0
    
    return {
        'symbol': symbol,
        'name': trades[0].get('name', symbol),
        'trades': trades,
        'total_return': total_return,
        'win_rate': win_rate,
        'total_trades': len(sell_trades),
        'wins': len(wins),
        'losses': len(sell_trades) - len(wins),
        'avg_win': sum(t['pnl_pct'] for t in wins) / len(wins) if wins else 0,
        'avg_loss': sum(t['pnl_pct'] for t in sell_trades if t['pnl_pct'] < 0) / (len(sell_trades) - len(wins)) if sell_trades else 0,
    }

# ========== 涨停股池选股 ==========
def find_hot_stocks(date_str=None):
    """从涨停股中找强势回调机会"""
    if date_str is None:
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime('%Y%m%d')
    
    zt_stocks = get_zt_pool(date_str)
    if not zt_stocks:
        return []
    
    # 找涨停后回调的股票
    results = []
    for stock in zt_stocks[:20]:  # 只看前20只
        sym = stock['code']
        secid = f"1.{sym}" if sym.startswith('6') else f"0.{sym}"
        klines = get_kline(secid, 30)
        if not klines or len(klines) < 5:
            continue
        
        closes = [k['close'] for k in klines]
        rsi = calc_rsi(closes)
        vol_r = calc_vol_ratio([k['volume'] for k in klines])
        ma5 = calc_ma(closes, 5)
        
        # 涨停后缩量回调
        if stock['chg_pct'] > 9 and vol_r < 0.8 and rsi and 30 < rsi < 50:
            results.append({
                'symbol': sym,
                'name': stock['name'],
                'zt_date': date_str,
                'zt_chg': stock['chg_pct'],
                'price': stock['price'],
                'rsi': rsi,
                'vol_r': vol_r,
                'ma5': ma5,
                'recommendation': '📈 涨停缩量回调，关注',
            })
        
        time.sleep(0.2)
    
    return results

# ========== 主信号扫描 ==========
def run_scan():
    """执行完整扫描"""
    portfolio = json.load(open(CONFIG_FILE)) if CONFIG_FILE.exists() else {}
    symbols = list(portfolio.keys())
    
    print("🔍 扫描股票池...")
    results = scan_stocks(symbols)
    
    # 按信号分类
    buys = [r for r in results if r['signal'] == 'BUY']
    sells = [r for r in results if r['signal'] == 'SELL']
    watch = [r for r in results if r['signal'] == 'WATCH']
    holds = [r for r in results if r['signal'] == 'HOLD']
    
    print(f"\n{'='*60}")
    print(f"📊 扫描报告  {datetime.now().strftime('%m-%d %H:%M')}")
    print(f"{'='*60}")
    
    if buys:
        print(f"\n🚀 买入信号 ({len(buys)}只):")
        for r in buys:
            print(f"  {r['symbol']} {r['name']:<8} 现价:{r['price']:.2f} 今日:{r['chg_today']:+.2f}% RSI:{r['rsi']:.0f} {r['reason']}")
    
    if watch:
        print(f"\n👀 关注 ({len(watch)}只):")
        for r in watch:
            print(f"  {r['symbol']} {r['name']:<8} {r['reason']}")
    
    if sells:
        print(f"\n⚠️ 卖出信号 ({len(sells)}只):")
        for r in sells:
            print(f"  {r['symbol']} {r['name']:<8} {r['reason']}")
    
    if holds:
        print(f"\n⏸️ 观望 ({len(holds)}只):")
        for r in holds:
            print(f"  {r['symbol']} {r['name']:<8} {r['reason']}")
    
    # 保存信号
    signal_data = {
        'timestamp': datetime.now().isoformat(),
        'buys': buys,
        'sells': sells,
        'watch': watch,
        'holds': holds,
    }
    with open(SIGNALS_FILE, 'w') as f:
        json.dump(signal_data, f, ensure_ascii=False, indent=2)
    
    return signal_data

def run_backtest():
    """运行回测"""
    portfolio = json.load(open(CONFIG_FILE)) if CONFIG_FILE.exists() else {}
    symbols = list(portfolio.keys())
    
    print(f"📈 回测: {len(symbols)} 只股票\n")
    all_results = []
    
    for sym in symbols:
        print(f"  回测 {sym}...", end=" ", flush=True)
        result = backtest(sym, '2025-01-01', 100000)
        if result:
            all_results.append(result)
            trades = result['total_trades']
            ret = result['total_return']
            wr = result['win_rate']
            print(f"交易{trades}次 胜率{wr:.0f}% 收益{ret:+.1f}%")
        else:
            print("数据不足")
        time.sleep(0.3)
    
    # 排序
    all_results.sort(key=lambda x: x['total_return'], reverse=True)
    
    print(f"\n{'='*60}")
    print(f"📊 回测汇总 (2025-01-01至今)")
    print(f"{'='*60}")
    print(f"{'代码':<8} {'总收益':>8} {'交易次数':>8} {'胜率':>6} {'均盈':>6} {'均亏':>6}")
    print("-" * 50)
    for r in all_results:
        print(f"{r['symbol']:<8} {r['total_return']:>+7.1f}% {r['total_trades']:>6}次 {r['win_rate']:>5.0f}% {r['avg_win']:>+5.1f}% {r['avg_loss']:>+5.1f}%")
    
    total_return_avg = sum(r['total_return'] for r in all_results) / len(all_results)
    print(f"\n平均收益: {total_return_avg:+.1f}%")
    
    with open(BACKTEST_FILE, 'w') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

# ========== 命令行 ==========
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 quant_system.py scan      - 扫描信号")
        print("  python3 quant_system.py backtest  - 运行回测")
        print("  python3 quant_system.py hot       - 找涨停回调股")
        print("  python3 quant_system.py add 600519 - 添加股票")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == 'scan':
        run_scan()
    elif cmd == 'backtest':
        run_backtest()
    elif cmd == 'hot':
        results = find_hot_stocks()
        if results:
            print(f"📈 涨停回调机会 ({len(results)}只):")
            for r in results:
                print(f"  {r['symbol']} {r['name']} RSI={r['rsi']:.0f} 量比={r['vol_r']:.1f}x {r['recommendation']}")
        else:
            print("今日涨停股池获取失败或无回调机会")
    elif cmd == 'add' and len(sys.argv) >= 3:
        sym = sys.argv[2]
        name = sys.argv[3] if len(sys.argv) > 3 else sym
        portfolio = json.load(open(CONFIG_FILE)) if CONFIG_FILE.exists() else {}
        portfolio[sym] = {'name': name, 'alert_pct': 5.0, 'alert_direction': 'both', 'added_at': datetime.now().strftime('%Y-%m-%d %H:%M')}
        json.dump(portfolio, open(CONFIG_FILE, 'w'), ensure_ascii=False, indent=2)
        print(f"✅ 添加 {sym} {name}")
