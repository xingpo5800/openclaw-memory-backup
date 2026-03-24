#!/usr/bin/env python3
"""
个股智能诊断系统 - Web版 v1.0
Flask Web服务
"""
import sys, json, re
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine.data_fetch import get_realtime, get_kline
from engine.indicators import calc_all_indicators
from engine.diagnosis import run_diagnosis
from engine.fundamentals import get_fundamentals

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# ========== 首页 ==========
@app.route('/')
def index():
    return render_template('index.html')

# ========== 诊断API ==========
@app.route('/api/diagnose', methods=['POST'])
def api_diagnose():
    data = request.get_json()
    code = data.get('code', '').strip().zfill(6)
    indicators = data.get('indicators', [])
    
    if not code:
        return jsonify({'error': '请输入股票代码'})
    
    rt = get_realtime(code)
    kl = get_kline(code, 120)
    
    if not rt:
        return jsonify({'error': f'无法获取股票 {code} 的数据'})
    if len(kl) < 30:
        return jsonify({'error': f'K线数据不足（{len(kl)}天），无法分析'})
    
    ind_data = calc_all_indicators(kl)
    diag = run_diagnosis(rt, kl, ind_data, indicators)
    
    fund = {}
    if 'fundamentals' in indicators:
        fund = get_fundamentals(code)
    
    return jsonify({
        'success': True,
        'stock': {
            'name': rt['name'],
            'code': code,
            'price': rt['price'],
            'chg_pct': rt['chg_pct'],
            'prev_close': rt['prev_close'],
            'open': rt['open'],
            'high': rt['high'],
            'low': rt['low'],
            'vol': rt['vol'],
            'turnover': rt.get('turnover'),
            'pe': rt.get('pe'),
            'pb': rt.get('pb'),
            'date': rt['date'],
            'time': rt['time'],
        },
        'indicators': ind_data,
        'diagnosis': diag,
        'fundamentals': fund,
    })

# ========== 搜索API ==========
@app.route('/api/search', methods=['GET'])
def api_search():
    keyword = request.args.get('q', '').strip().lower()
    if not keyword:
        return jsonify({'results': []})
    
    codes = [
        ('000001', '平安银行'), ('000002', '万科A'), ('000004', '国华网安'),
        ('000005', 'ST星源'), ('000006', '深振业A'), ('000858', '五粮液'),
        ('002594', '比亚迪'), ('002230', '科大讯飞'), ('002241', '歌尔股份'),
        ('002475', '立讯精密'), ('300750', '宁德时代'), ('300059', '东方财富'),
        ('300124', '汇川技术'), ('300274', '阳光电源'), ('300830', '金现代'),
        ('002865', '钧达股份'), ('002202', '金风科技'), ('002487', '大金重工'),
        ('600519', '贵州茅台'), ('600036', '招商银行'), ('600276', '恒瑞医药'),
        ('600900', '长江电力'), ('601318', '中国平安'), ('601888', '中国中免'),
        ('603259', '药明康德'), ('688981', '中芯国际'),
    ]
    
    results = [
        {'code': c, 'name': n, 'market': '沪深'}
        for c, n in codes
        if keyword in c or keyword in n.lower()
    ]
    return jsonify({'results': results[:10]})

# ========== 健康检查 ==========
@app.route('/api/health')
def api_health():
    return jsonify({'status': 'ok', 'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

# ========== 启动 ==========
if __name__ == '__main__':
    port = 5015
    print(f"个股诊断系统启动中...")
    print(f"访问地址: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
