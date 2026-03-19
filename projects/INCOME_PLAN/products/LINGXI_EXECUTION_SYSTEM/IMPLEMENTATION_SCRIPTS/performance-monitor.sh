#!/bin/bash
# 性能监控脚本

# 监控指标
declare -A MONITORING_METRICS
MONITORING_METRICS["response_time"]=0
MONITORING_METRICS["tool_calls"]=0
MONITORING_METRICS["tokens_used"]=0
MONITORING_METRICS["execution_efficiency"]=0

# 监控数据存储
MONITOR_DATA_DIR="/Users/kevin/.openclaw/workspace/projects/INCOME_PLAN/monitoring"
REPORT_FILE="$MONITOR_DATA_DIR/daily_report_$(date +%Y%m%d).md"

# 创建数据目录
mkdir -p "$MONITOR_DATA_DIR"

# 记录监控数据
log_metric() {
    local metric_name="$1"
    local metric_value="$2"
    local timestamp="$(date -Iseconds)"
    
    echo "$timestamp,$metric_name,$metric_value" >> "$MONITOR_DATA_DIR/metrics.csv"
    
    # 更新内存中的指标
    MONITORING_METRICS["$metric_name"]="$metric_value"
}

# 生成日报
generate_daily_report() {
    local date_str="$(date +%Y-%m-%d)"
    
    echo "# 📊 灵犀系统性能日报 - $date_str" > "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "## 监控概览" >> "$REPORT_FILE"
    
    # 读取今天的监控数据
    local today_data=$(grep "$(date +%Y-%m-%d)" "$MONITOR_DATA_DIR/metrics.csv")
    
    if [[ -z "$today_data" ]]; then
        echo "暂无今日数据" >> "$REPORT_FILE"
        return
    fi
    
    # 计算平均值
    local avg_response_time=$(echo "$today_data" | grep ",response_time," | cut -d',' -f3 | awk '{sum+=$1} END {print sum/NR}' 2>/dev/null || echo "0")
    local avg_tool_calls=$(echo "$today_data" | grep ",tool_calls," | cut -d',' -f3 | awk '{sum+=$1} END {print sum/NR}' 2>/dev/null || echo "0")
    local avg_tokens_used=$(echo "$today_data" | grep ",tokens_used," | cut -d',' -f3 | awk '{sum+=$1} END {print sum/NR}' 2>/dev/null || echo "0")
    local avg_efficiency=$(echo "$today_data" | grep ",execution_efficiency," | cut -d',' -f3 | awk '{sum+=$1} END {print sum/NR}' 2>/dev/null || echo "0")
    
    # 生成报告
    echo "| 指标 | 平均值 |" >> "$REPORT_FILE"
    echo "|------|--------|" >> "$REPORT_FILE"
    printf "| 平均响应时间 | %.2f秒 |\n" "$avg_response_time" >> "$REPORT_FILE"
    printf "| 平均工具调用 | %.1f次 |\n" "$avg_tool_calls" >> "$REPORT_FILE"
    printf "| 平均Tokens使用 | %.0f |\n" "$avg_tokens_used" >> "$REPORT_FILE"
    printf "| 执行效率 | %.1f%% |\n" "$avg_efficiency" >> "$REPORT_FILE"
    
    echo "" >> "$REPORT_FILE"
    echo "## 优化建议" >> "$REPORT_FILE"
    
    if (( $(echo "$avg_response_time > 20" | bc -l 2>/dev/null || echo "1") )); then
        echo "- ⚠️  响应时间偏长，建议优化认知层处理速度" >> "$REPORT_FILE"
    fi
    
    if (( $(echo "$avg_tool_calls > 3" | bc -l 2>/dev/null || echo "1") )); then
        echo "- ⚠️  工具调用过多，建议加强记忆检索" >> "$REPORT_FILE"
    fi
    
    if (( $(echo "$avg_tokens_used > 100000" | bc -l 2>/dev/null || echo "1") )); then
        echo "- ⚠️  Tokens消耗较高，建议优化上下文管理" >> "$REPORT_FILE"
    fi
    
    if (( $(echo "$avg_efficiency < 80" | bc -l 2>/dev/null || echo "1") )); then
        echo "- ⚠️  执行效率偏低，建议检查执行流程" >> "$REPORT_FILE"
    fi
    
    if (( $(echo "$avg_efficiency > 90" | bc -l 2>/dev/null || echo "0") )); then
        echo "- ✅ 执行效率优秀，保持当前优化策略" >> "$REPORT_FILE"
    fi
    
    echo "" >> "$REPORT_FILE"
    echo "## 数据来源" >> "$REPORT_FILE"
    echo "- 监控数据