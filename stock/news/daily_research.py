#!/usr/local/bin/python3
"""
每日股市研究报告生成
每天9:15前自动运行
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime

# 生成日报文件名
today = datetime.now().strftime('%Y-%m-%d')
report_path = f"/Users/kevin/.openclaw/workspace/stock/news/{today}-早报.md"

# 检查是否已存在
if os.path.exists(report_path):
    print(f"今日早报已存在: {report_path}")
    sys.exit(0)

# 简单占位日报（完整日报由cron任务生成）
with open(report_path, 'w') as f:
    f.write(f"""# 每日早报

> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}

## 开盘前检查

### 大盘趋势
请运行：
```bash
cd /Users/kevin/.openclaw/workspace/stock && python3 quant_system.py scan
```

### 国际市场
请检查：纳斯达克、原油、黄金、美元

### 新闻摘要
请检查新浪财经头条

### 今日操作计划
待填写...

---
*自动生成*
""")

print(f"✅ 今日早报模板已创建: {report_path}")
