#!/usr/local/bin/python3
"""
A股监控系统 v2.0
功能：
  - 实时行情监控
  - 涨跌幅提醒
  - 定时检查（cron）
  - 历史K线记录
  - 缠论笔段分析
  - 缠论中枢识别
  - 缠论背驰判断 + 三类买卖点 + 综合评分

用法：
  python3 monitor.py list                    # 查看关注列表
  python3 monitor.py add 600519              # 添加股票
  python3 monitor.py watch                  # 实时监控一次
  python3 monitor.py loop                    # 循环监控（Ctrl+C停止）
  python3 monitor.py history 600519          # 查看历史K线
  python3 monitor.py chan 002929             # 缠论完整分析
  python3 monitor.py chan 002929 --days 250 # 分析最近250天
  python3 monitor.py chan 002929 --raw       # 显示K线处理详情
  python3 monitor.py zhongshu 605117        # 中枢专项分析
  python3 monitor.py beichi 605117          # 背驰专项分析+三类买卖点+综合评分
  python3 monitor.py hot                    # 强势股择优（涨幅前10缠论评分+综合排序）
  python3 monitor.py hot --top=5            # 只对涨幅前5只评分（更快）
  python3 monitor.py hot --debug            # 显示调试信息
"""

import requests
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# WORKSPACE 定义在下面，chan 导入放在 main() 入口处（延迟导入避免顺序问题）
chan_module = None

# ========== 配置 ==========
WORKSPACE = Path(__file__).parent
CONFIG_FILE = WORKSPACE / "portfolio.json"
HISTORY_DIR = WORKSPACE / "history"
CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

# 东方财富API
EASTMONEY_URL = "https://push2.eastmoney.com/api/qt/ulist.np/get"
EASTMONEY_SINGLE = "https://push2.eastmoney.com/api/qt/stock/get"

# ========== 工具函数 ==========
def price_fmt(c):
    """分转元（东方财富返回的单位是厘，除以100得元）"""
    return c / 100 if isinstance(c, (int, float)) and c else 0

def get_batch_data(secids):
    """批量获取实时行情"""
    if not secids:
        return []
    secid_str = ",".join(secids)
    params = {
        'secids': secid_str,
        'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
        'fields': 'f2,f3,f4,f5,f6,f12,f14,f15,f16,f17,f18,f62',
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'Referer': 'https://quote.eastmoney.com/'
    }
    try:
        r = requests.get(EASTMONEY_URL, params=params, headers=headers, timeout=10)
        data = r.json()
        return data.get('data', {}).get('diff', [])
    except Exception as e:
        print(f"❌ API错误: {e}")
        return []

def get_history_kline(secid, days=30):
    """获取日K历史数据"""
    # secid: 1.600519(沪), 0.000001(深)
    url = "https://push2.eastmoney.com/api/qt/stock/kline/get"
    params = {
        'secid': secid,
        'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
        'fields1': 'f1,f2,f3,f4,f5,f6',
        'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
        'klt': '101',  # 日线
        'fqt': '1',    # 前复权
        'end': '20500101',
        'lmt': str(days)
    }
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://quote.eastmoney.com/'
    }
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        raw = r.json().get('data', {}).get('klines', [])
        result = []
        for line in raw:
            parts = line.split(',')
            if len(parts) >= 6:
                result.append({
                    'date': parts[0],
                    'open': float(parts[1]) / 100,
                    'close': float(parts[2]) / 100,
                    'high': float(parts[3]) / 100,
                    'low': float(parts[4]) / 100,
                    'volume': int(parts[5]) if parts[5] else 0,
                })
        return result
    except Exception as e:
        print(f"❌ 历史数据错误: {e}")
        return []

# ========== 组合管理 ==========
def load_portfolio():
    """加载关注组合"""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}

def save_portfolio(portfolio):
    """保存组合"""
    CONFIG_FILE.write_text(json.dumps(portfolio, ensure_ascii=False, indent=2))

def secid_to_market(symbol):
    """判断市场：沪1，深0"""
    symbol = symbol.strip()
    if symbol.startswith(('6', '5', '9', '7')):
        return f"1.{symbol}"
    else:
        return f"0.{symbol}"

def add_stock(symbol, name=None, alert_pct=5.0, alert_direction='both', note=None):
    """添加股票到监控列表"""
    portfolio = load_portfolio()
    if symbol not in portfolio:
        portfolio[symbol] = {
            'name': name or symbol,
            'alert_pct': alert_pct,
            'alert_direction': alert_direction,  # up, down, both
            'last_price': None,
            'note': note,  # 追踪备注（如：强势股择优验证，缠论分=0）
            'last_chg': None,
            'added_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        }
        save_portfolio(portfolio)
        print(f"✅ 添加 {symbol} 到监控列表")
    else:
        print(f"⚠️ {symbol} 已在列表中")

def remove_stock(symbol):
    """移除股票"""
    portfolio = load_portfolio()
    if symbol in portfolio:
        del portfolio[symbol]
        save_portfolio(portfolio)
        print(f"✅ 移除 {symbol}")
    else:
        print(f"⚠️ {symbol} 不在列表中")

# ========== 监控核心 ==========
def get_watch_list():
    """获取监控列表"""
    portfolio = load_portfolio()
    if not portfolio:
        print("⚠️ 监控列表为空，先添加: python3 monitor.py add 股票代码")
        return []
    return portfolio

def watch_once():
    """执行一次监控"""
    portfolio = get_watch_list()
    if not portfolio:
        return
    
    # 构造secids
    secids = [secid_to_market(s) for s in portfolio.keys()]
    stocks = get_batch_data(secids)
    
    if not stocks:
        print("❌ 获取数据失败")
        return
    
    now = datetime.now().strftime('%m-%d %H:%M')
    print(f"\n{'='*60}")
    print(f"📊 A股实时行情  {now}")
    print(f"{'='*60}")
    print(f"{'代码':<8} {'名称':<10} {'现价':>8} {'涨跌额':>8} {'涨跌幅':>8} {'状态'}")
    print(f"{'-'*60}")
    
    alerts = []
    for s in stocks:
        symbol = str(s.get('f12', ''))
        name = s.get('f14', '?')
        price = price_fmt(s.get('f2', 0))
        prev_close = price_fmt(s.get('f18', 0))
        chg_val = price - prev_close if prev_close else 0
        chg_pct_val = (chg_val / prev_close * 100) if prev_close else 0
        
        # 状态
        status = "📊"
        if chg_pct_val > 9.5:
            status = "🔴涨停"
        elif chg_pct_val > 5:
            status = "🚀大涨"
        elif chg_pct_val > 0:
            status = "🟢上涨"
        elif chg_pct_val < -5:
            status = "🔵大跌"
        elif chg_pct_val < -9.5:
            status = "⚫跌停"
        elif chg_pct_val < 0:
            status = "🔴下跌"
        else:
            status = "➖平"
        
        # 检查提醒
        cfg = portfolio.get(symbol, {})
        alert_pct = cfg.get('alert_pct', 5.0)
        alert_dir = cfg.get('alert_direction', 'both')
        
        if abs(chg_pct_val) >= alert_pct:
            if alert_dir in ('both', 'up') and chg_pct_val > 0:
                alerts.append(f"🚨 {name} 上涨 {chg_pct_val:+.2f}%")
            if alert_dir in ('both', 'down') and chg_pct_val < 0:
                alerts.append(f"🚨 {name} 下跌 {chg_pct_val:+.2f}%")
        
        print(f"{symbol:<8} {name:<10} {price:>8.2f} {chg_val:>+8.2f} {chg_pct_val:>+7.2f}% {status}")
    
    print(f"{'='*60}")
    
    if alerts:
        print("\n🚨 预警提醒:")
        for a in alerts:
            print(f"  {a}")
    else:
        print("\n✅ 无预警")

def loop_watch(interval=30):
    """循环监控"""
    print(f"🔄 开始循环监控（间隔{interval}秒，Ctrl+C停止）")
    try:
        while True:
            watch_once()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\n⏹️ 停止监控")

def show_history(symbol, days=30):
    """显示历史K线"""
    secid = secid_to_market(symbol)
    data = get_history_kline(secid, days)
    if not data:
        print(f"❌ 获取 {symbol} 历史数据失败")
        return
    
    portfolio = load_portfolio()
    name = portfolio.get(symbol, {}).get('name', symbol)
    
    print(f"\n📈 {name}({symbol}) 近{days}日K线")
    print(f"{'-'*70}")
    print(f"{'日期':<12} {'开':>8} {'收':>8} {'高':>8} {'低':>8} {'成交量':>10}")
    print(f"{'-'*70}")
    
    for d in reversed(data[-20:]):  # 显示最近20天
        print(f"{d['date']:<12} {d['open']:>8.2f} {d['close']:>8.2f} {d['high']:>8.2f} {d['low']:>8.2f} {d['volume']:>10,}")
    
    # 技术指标简单计算
    closes = [d['close'] for d in data]
    if len(closes) >= 5:
        ma5 = sum(closes[-5:]) / 5
        ma10 = sum(closes[-10:]) / 10 if len(closes) >= 10 else ma5
        ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else ma10
        latest = closes[-1]
        print(f"\n📊 均线: MA5={ma5:.2f} MA10={ma10:.2f} MA20={ma20:.2f}")
        if latest > ma5 > ma10:
            print("🎯 均线多头排列，上涨趋势")
        elif latest < ma5 < ma10:
            print("🎯 均线空头排列，下降趋势")
        else:
            print("🎯 均线纠缠，震荡整理")

# ========== 命令行入口 ==========
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == 'list':
        portfolio = load_portfolio()
        if not portfolio:
            print("监控列表为空")
            return
        print(f"📋 监控列表 ({len(portfolio)} 只):")
        for sym, info in portfolio.items():
            print(f"  {sym:<8} {info['name']:<12} 预警:{info['alert_pct']}% {info['alert_direction']}")
    
    elif cmd == 'add' and len(sys.argv) >= 3:
        symbol = sys.argv[2].strip()
        name = sys.argv[3] if len(sys.argv) > 3 else None
        alert_pct = float(sys.argv[4]) if len(sys.argv) > 4 else 5.0
        add_stock(symbol, name, alert_pct)
    
    elif cmd == 'remove' and len(sys.argv) >= 3:
        remove_stock(sys.argv[2])
    
    elif cmd == 'watch':
        watch_once()
    
    elif cmd == 'loop':
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        loop_watch(interval)
    
    elif cmd == 'history' and len(sys.argv) >= 3:
        symbol = sys.argv[2].strip()
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
        show_history(symbol, days)
    
    elif cmd in ('chan', 'zhongshu', 'beichi'):
        global chan_module
        if chan_module is None:
            sys.path.insert(0, str(WORKSPACE))
            try:
                import chan as chan_module
            except Exception as e:
                print(f"❌ 缠论模块加载失败: {e}")
                return

        if len(sys.argv) < 3:
            print("用法: python3 monitor.py chan 股票代码 [--days N] [--raw]")
            print("  例: python3 monitor.py chan 002929")
            print("  例: python3 monitor.py chan 002929 --days 120 --raw")
            print("  例: python3 monitor.py zhongshu 002929  # 仅中枢分析")
            print("  例: python3 monitor.py beichi 002929   # 仅背驰分析")
        else:
            symbol = sys.argv[2].strip()
            days = 120
            show_raw = False
            args = sys.argv[3:]
            i = 0
            while i < len(args):
                if args[i] == '--days' and i + 1 < len(args):
                    days = int(args[i + 1]); i += 2
                elif args[i] == '--raw':
                    show_raw = True; i += 1
                else:
                    i += 1

            # chan命令走完整分析
            if cmd == 'chan':
                result = chan_module.analyze(symbol, days, show_raw)
                if result:
                    print(f"\n💡 缠论完整分析: 笔数={len(result['bis'])} | 线段={len(result['segs'])} | "
                          f"中枢={len(result['zhongshu'])} | 背驰={len(result['beichi'])}")
                    print(f"   综合评分: {result['score']['score']:.1f}/10 → {result['score']['recommendation']}")
            else:
                # zhongshu/beichi 仅显示专项分析
                secid = chan_module.secid_of(symbol)
                klines = chan_module.get_kline(secid, days)
                if not klines:
                    print(f"❌ 获取 {symbol} 数据失败"); return
                bis = chan_module.identify_bi(klines)
                zhongshu_list = chan_module.find_zhongshu(bis)
                macd_data = chan_module.calc_macd_for_bis(klines, bis)
                beichi_signals = chan_module.find_beichi(bis, zhongshu_list, macd_data)

                print(f"\n{'='*70}")
                print(f"🏛️  中枢分析  {symbol}  ({klines[0]['date']} → {klines[-1]['date']})")
                print(f"{'='*70}")
                chan_module.print_zhongshu(zhongshu_list)

                if cmd == 'beichi':
                    print(f"\n{'='*70}")
                    print(f"⚡ 背驰分析  {symbol}")
                    print(f"{'='*70}")
                    chan_module.print_beichi(beichi_signals)
                    maidian = chan_module.find_maidian(bis, zhongshu_list, beichi_signals, klines=klines)
                    chan_module.print_maidian(maidian)
                    score = chan_module.calc_comprehensive_score(bis, zhongshu_list, beichi_signals, maidian, klines)
                    chan_module.print_score(score)

    elif cmd == 'integrate':
        # 综合分析：缠论 + RSI + MACD
        if chan_module is None:
            sys.path.insert(0, str(WORKSPACE))
            try:
                import chan as chan_module
            except Exception as e:
                print(f"❌ 缠论模块加载失败: {e}"); return

        symbol = sys.argv[2].strip() if len(sys.argv) > 2 else ''
        if not symbol:
            portfolio = load_portfolio()
            if portfolio:
                print(f"📋 综合分析 - 全部持仓股票:")
                for sym, info in portfolio.items():
                    chan_module.print_integrated(sym, 120, '240')
            return

        days = 120; scale = '240'
        for a in sys.argv[3:]:
            if a.startswith('--days='): days = int(a.split('=')[1])
            elif a == '--30min': scale = '30'
            elif a == '--60min': scale = '60'
        chan_module.print_integrated(symbol, days, scale)

    elif cmd == 'hot':
        # 强势股择优
        try:
            sys.path.insert(0, str(WORKSPACE))
            import market_hot as mh
        except Exception as e:
            print(f"❌ market_hot 模块加载失败: {e}")
            return

        top_n = 10
        debug = False
        args = sys.argv[2:]
        i = 0
        while i < len(args):
            if args[i].startswith('--top='):
                top_n = int(args[i].split('=')[1]); i += 1
            elif args[i] == '--debug':
                debug = True; i += 1
            else:
                i += 1

        mh.analyze_hot_stocks(top_n=top_n, debug=debug)

    elif cmd == 'init':
        # 初始化示例组合
        demo_stocks = [
            ('600519', '贵州茅台', 3.0),
            ('000001', '平安银行', 3.0),
            ('002594', '比亚迪', 4.0),
            ('300750', '宁德时代', 4.0),
        ]
        portfolio = {}
        for sym, name, alert in demo_stocks:
            portfolio[sym] = {
                'name': name,
                'alert_pct': alert,
                'alert_direction': 'both',
                'added_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
            }
        save_portfolio(portfolio)
        print(f"✅ 已初始化示例组合: {len(demo_stocks)} 只股票")
    
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)

if __name__ == '__main__':
    main()
