#!/usr/local/bin/python3
"""
强势股择优模块 v1.0
功能：
  - 从东方财富接口获取A股涨幅前30
  - 过滤涨停股（涨幅>=9.9%，买不进去）
  - 按涨幅排序 + 缠论综合评分综合排序
  - 输出TOP3买入建议

用法：
  python3 market_hot.py              # 强势股择优（默认前30取前10评分）
  python3 market_hot.py --top=5      # 只取涨幅前5评分（更快）
  python3 market_hot.py --debug      # 显示调试信息
"""

import requests
import sys
import json
import time
import math
from datetime import datetime

# ========== 配置 ==========
WORKSPACE_DIR = "/Users/kevin/.openclaw/workspace/stock"
SINA_HOT_URL = "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData"

# 缠论评分权重
CHAN_WEIGHT = 0.60   # 缠论综合分权重
GAIN_WEIGHT = 0.40   # 涨幅权重

# 涨停阈值（涨幅>=此值视为涨停）
LIMIT_UP_THRESHOLD = 9.9


# ========== 新浪财经涨幅榜接口 ==========
def fetch_top_gainers(limit=30):
    """
    获取A股涨幅前N名（非ST、非退市）
    按涨幅降序排列。翻页到足够深以获取足够的非涨停股票。
    返回: [{symbol, name, price, chg_pct, prev_close}, ...]
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'Referer': 'https://finance.sina.com.cn/',
    }

    all_stocks = []
    page = 1
    max_pages = 15  # 最多翻15页（约450只），应能覆盖足够多
    page_size = 30
    non_limitup_count = 0
    # 至少需要找到 top_n*3 只非涨停股票才停止（确保有足够的非涨停候选）
    min_non_limitup = max(limit * 5, 60)  # 提高阈值确保翻到非涨停区间

    print(f"📡 正在从新浪财经获取A股涨幅排行...")
    while page <= max_pages:
        params = {
            'page': page,
            'num': page_size,
            'sort': 'changepercent',
            'asc': 0,
            'node': 'hs_a',
            'symbol': '',
            '_s_r_a': 'page',
        }
        try:
            r = requests.get(SINA_HOT_URL, params=params, headers=headers, timeout=15)
            r.encoding = 'gbk'
            raw = r.json()
            if not raw or not isinstance(raw, list) or len(raw) == 0:
                break

            for s in raw:
                chg_pct = float(s.get('changepercent', 0) or 0)
                name = s.get('name', '')
                price = float(s.get('trade', 0) or 0)
                if price <= 0:
                    continue
                # 过滤ST、退市股
                if 'ST' in name or '退' in name or name.startswith('*'):
                    continue

                prev_close = float(s.get('settlement', 0) or 0)
                if prev_close <= 0:
                    prev_close = price / (1 + chg_pct / 100) if chg_pct != 0 else price

                # symbol: 去掉 sh/sz 前缀，转纯6位代码
                full_sym = s.get('symbol', '')
                code = full_sym.replace('sh', '').replace('sz', '')

                stock = {
                    'symbol': code,
                    'name': name,
                    'price': price,
                    'chg_pct': chg_pct,
                    'prev_close': prev_close,
                    'high': float(s.get('high', 0) or 0),
                    'low': float(s.get('low', 0) or 0),
                    'volume': int(s.get('volume', 0) or 0),
                    'amount': float(s.get('amount', 0) or 0),
                    'open': float(s.get('open', 0) or 0),
                }
                all_stocks.append(stock)
                if chg_pct < LIMIT_UP_THRESHOLD:
                    non_limitup_count += 1

            # 当收集到足够的非涨停股票时停止（同时也受max_pages限制）
            if non_limitup_count >= min_non_limitup:
                break
            if len(raw) < page_size:
                break
            page += 1
            time.sleep(0.15)

        except Exception as e:
            print(f"❌ 第{page}页API错误: {e}")
            break

    # 返回涨幅前limit只（非涨停优先，取足量后再过滤）
    non_limitup = [s for s in all_stocks if s['chg_pct'] < LIMIT_UP_THRESHOLD]
    # 如果非涨停不足，返回全部；否则取前limit只
    if len(non_limitup) >= limit:
        return non_limitup[:limit]
    # 非涨停不够，返回所有非涨停（已按涨幅降序）
    return non_limitup if non_limitup else all_stocks[:limit]


def secid_of(symbol):
    """股票代码 → secid格式"""
    s = symbol.strip().zfill(6)
    if s.startswith(('6', '5', '9', '7')):
        return f"1.{s}"
    return f"0.{s}"


# ========== 缠论综合评分（复用 chan.py）==========
def get_chan_score(symbol, days=120):
    """
    调用 chan.calc_integrated_score 获取综合评分
    返回: {score, recommendation, entry_price, stop_loss, rsi, macd, signals}
    """
    try:
        sys.path.insert(0, WORKSPACE_DIR)
        import chan as chan_module
        result = chan_module.calc_integrated_score(symbol, days)
        return result
    except Exception as e:
        return {'error': str(e), 'score': 0}


def calc_composite_score(stock_info, chan_result):
    """
    综合分 = 涨幅权重40% + 缠论综合分60%
    涨幅分：将涨幅归一化到0-100区间（涨幅越大分越高）
    缠论分：直接用chan的0-100分
    """
    chg_pct = stock_info['chg_pct']

    # 涨幅分：涨幅3%-10%映射到0-100（过滤了涨停，所以上限9.9%）
    # 分段: 0%=0分, 3%=30分, 6%=60分, 9.9%=100分
    chg_score = min(chg_pct / LIMIT_UP_THRESHOLD * 100, 100)

    if 'error' in chan_result or chan_result.get('score', 0) == 0:
        chan_score = 0
    else:
        chan_score = chan_result['score']

    composite = round(chg_score * GAIN_WEIGHT + chan_score * CHAN_WEIGHT, 2)
    return {
        'chg_score': round(chg_score, 1),
        'chan_score': chan_score,
        'composite': composite,
    }


# ========== 买入建议 ==========
def generate_buy_advice(stock, chan_result):
    """
    生成买入建议
    - 买入价：当前价（或开盘价参考）
    - 止损价：缠论止损 或 当前价-5%
    - 预期涨幅：根据综合分估算
    """
    price = stock['price']
    composite = stock['composite']

    # 止损：取缠论止损和固定止损的更严格值
    if chan_result.get('stop_loss'):
        stop_loss = chan_result['stop_loss']
    else:
        stop_loss = round(price * 0.95, 2)

    # 预期涨幅：根据评分估算
    if composite >= 75:
        expected_gain = 8.0
        risk_ratio = "高赔率"
    elif composite >= 60:
        expected_gain = 5.0
        risk_ratio = "中高赔率"
    elif composite >= 50:
        expected_gain = 3.0
        risk_ratio = "中等赔率"
    else:
        expected_gain = 2.0
        risk_ratio = "低赔率"

    # 推荐理由
    reason_parts = []
    if 'signals' in chan_result:
        for sig in chan_result['signals'][:3]:
            reason_parts.append(sig)
    reason = ' | '.join(reason_parts) if reason_parts else '综合评分择优'

    return {
        'buy_price': round(price * 1.005, 2),  # 略高于现价（防跳价）
        'stop_loss': stop_loss,
        'expected_gain_pct': expected_gain,
        'risk_ratio': risk_ratio,
        'reason': reason,
    }


# ========== 主流程 ==========
def analyze_hot_stocks(top_n=10, debug=False):
    """
    强势股择优主流程
    1. 获取涨幅前30（深翻页，确保有足够非涨停）→ 过滤涨停
    2. 取前top_n（非涨停）做缠论评分
    3. 综合排序
    4. 输出TOP3买入建议
    """
    print(f"\n{'='*70}")
    print(f"🚀 强势股择优  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*70}")

    # Step 1: 获取涨幅前N（深翻页，确保有足够非涨停）
    all_stocks = fetch_top_gainers(limit=100)  # 取100只，深翻页
    if not all_stocks:
        print("❌ 获取数据失败")
        return

    # Step 2: 过滤涨停（涨幅>=9.9%，买不进去）
    non_limitup = [s for s in all_stocks if s['chg_pct'] < LIMIT_UP_THRESHOLD]
    limitup = [s for s in all_stocks if s['chg_pct'] >= LIMIT_UP_THRESHOLD]

    print(f"\n📊 涨幅榜概览：共获取 {len(all_stocks)} 只，涨停 {len(limitup)} 只（已过滤）")
    if limitup:
        limitup_names = [s['name'] for s in limitup[:8]]
        print(f"   🔴 涨停股（买不进去）: {', '.join(limitup_names)}" +
              (f" ...等{len(limitup)}只" if len(limitup) > 8 else ""))

    if not non_limitup:
        print("❌ 没有可买的非涨停股")
        return

    if not non_limitup:
        print("❌ 没有可买的非涨停股（市场极强！）")
        return

    # 取涨幅最高的前top_n只非涨停股做缠论评分
    score_candidates = non_limitup[:min(top_n, len(non_limitup))]
    print(f"\n🔍 正在对涨幅前{len(score_candidates)}只非涨停股做缠论综合评分...")

    scored = []
    for i, s in enumerate(score_candidates):
        sym = s['symbol']
        print(f"\n[{i+1}/{len(score_candidates)}] 正在分析 {sym} {s['name']}...", end='', flush=True)
        chan_result = get_chan_score(sym, days=120)
        if debug:
            print(f"\n    raw: {chan_result}")

        score_detail = calc_composite_score(s, chan_result)
        s.update(score_detail)
        s['chan_result'] = chan_result
        scored.append(s)

        # 进度显示
        if 'error' not in chan_result:
            print(f"  缠论分={chan_result.get('score',0):.0f} 综合分={score_detail['composite']:.1f}")
        else:
            print(f"  ⚠️ 缠论分析失败，综合分={score_detail['composite']:.1f}")
        time.sleep(0.2)

    # Step 4: 按综合分排序
    scored.sort(key=lambda x: x['composite'], reverse=True)

    # Step 5: 输出完整排名
    print(f"\n{'='*70}")
    print(f"📈 强势股综合评分排行（涨幅权重40% + 缠论60%）")
    print(f"{'='*70}")
    print(f"  {'排名':<4} {'代码':<8} {'名称':<10} {'涨幅':>7} {'缠论分':>6} {'综合分':>6} {'推荐理由'}")
    print(f"  {'-'*70}")

    for rank, s in enumerate(scored, 1):
        reason_parts = []
        if 'signals' in s.get('chan_result', {}):
            for sig in s['chan_result']['signals'][:2]:
                reason_parts.append(sig)
        reason = ' '.join(reason_parts) if reason_parts else '-'
        print(f"  {rank:<4} {s['symbol']:<8} {s['name']:<10} "
              f"{s['chg_pct']:>+6.1f}% {s['chan_score']:>6.0f} {s['composite']:>6.1f}  {reason}")

    # Step 6: TOP3买入建议
    top3 = scored[:3]
    print(f"\n{'='*70}")
    print(f"💰 TOP3 买入建议")
    print(f"{'='*70}")

    for rank, s in enumerate(top3, 1):
        advice = generate_buy_advice(s, s.get('chan_result', {}))
        print(f"\n  【第{rank}名】{s['name']}({s['symbol']})  综合分={s['composite']:.1f}")
        print(f"    📍 现价: {s['price']:.2f}  今日涨幅: {s['chg_pct']:+.2f}%")
        print(f"    ✅ 建议买入价: {advice['buy_price']:.2f}")
        print(f"    🔻 止损价: {advice['stop_loss']:.2f}  (跌破即出)")
        print(f"    🎯 预期涨幅: +{advice['expected_gain_pct']:.1f}%  ({advice['risk_ratio']})")
        print(f"    💡 推荐理由: {advice['reason']}")

        # 缠论信号
        chan_res = s.get('chan_result', {})
        if 'signals' in chan_res:
            print(f"    📊 信号: " + " | ".join(chan_res['signals'][:4]))
        if 'recommendation' in chan_res:
            print(f"    📐 缠论建议: {chan_res['recommendation']} (缠论分={chan_res['score']:.0f}/100)")

    print(f"\n{'='*70}")
    print(f"  ⚠️  风险提示：强势股波动大，请结合大盘环境，设定止损严格执行！")
    print(f"  📌 缠论评分基于120日数据，每日收盘后更新效果更佳")
    print(f"{'='*70}\n")

    return scored


# ========== 命令行入口 ==========
if __name__ == '__main__':
    top_n = 10
    debug = False

    for arg in sys.argv[1:]:
        if arg.startswith('--top='):
            top_n = int(arg.split('=')[1])
        elif arg == '--debug':
            debug = True

    analyze_hot_stocks(top_n=top_n, debug=debug)
