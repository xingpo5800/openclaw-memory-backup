# 基本面数据
import subprocess, json, re

def get_fundamentals(code):
    """获取基本面数据"""
    # 东方财富基本面API
    secid = f"0{code}" if code.startswith(('0','3')) else f"1{code}"
    url = f"https://push2.eastmoney.com/api/qt/slist/get?secid={secid}&fields=f12,f13,f14,f20,f21,f23,f37,f38,f45,f57,f58,f107,f116,f117,f162,f163,f164,f166,f167,f168,f169"
    
    r = subprocess.run(["curl", "-s", url], capture_output=True)
    try:
        data = json.loads(r.stdout)
        diff = data.get('data', {}).get('diff', [{}])
        if diff:
            d = diff[0] if isinstance(diff, list) else diff
            return {
                "pe": d.get('f23'),  # 市盈率
                "pb": d.get('f45'),  # 市净率
                "market_cap": d.get('f20'),  # 总市值
                "float_cap": d.get('f21'),  # 流通市值
                "roe": d.get('f37'),  # 净资产收益率
                "gross_margin": d.get('f38'),  # 毛利率
                "net_margin": d.get('f39') if 'f39' in d else None,  # 净利率
                "revenue_growth": d.get('f57'),  # 营收增长率
                "profit_growth": d.get('f58'),  # 利润增长率
            }
    except:
        pass
    
    return {}

def get_financial_summary(code):
    """财务摘要"""
    fund = get_fundamentals(code)
    
    if not fund:
        return "基本面数据获取失败"
    
    parts = []
    if fund.get('pe'):
        pe = float(fund['pe'])
        pe_desc = "低估" if pe < 15 else ("合理" if pe < 30 else "偏高")
        parts.append(f"PE={pe:.1f}（{pe_desc}）")
    if fund.get('roe'):
        roe = float(fund['roe'])
        roe_desc = "优秀" if roe > 15 else ("良好" if roe > 8 else "一般")
        parts.append(f"ROE={roe:.1f}%（{roe_desc}）")
    if fund.get('gross_margin'):
        gm = float(fund['gross_margin'])
        parts.append(f"毛利率={gm:.1f}%")
    
    return ' | '.join(parts) if parts else "数据不足"
