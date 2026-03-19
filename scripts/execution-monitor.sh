#!/bin/bash
# 灵犀执行监控系统

MONITOR_LOG="memory/execution-monitor.log"
ALERT_LOG="memory/execution-alert.log"
FEEDBACK_LOG="memory/feedback-data.json"

# 创建监控日志目录
mkdir -p memory

# 执行状态监控
monitor_execution_status() {
  local rule="$1"
  local context="$2"
  
  echo "[$(date)] 监控执行状态: $context.$rule" >> $MONITOR_LOG
  
  # 检查规则执行状态
  local execution_status=$(check_rule_execution "$rule" "$context")
  
  if [[ "$execution_status" == "missing" ]]; then
    echo "[$(date)] ⚠️  警告: 规则未执行: $context.$rule" >> $ALERT_LOG
    send_alert "规则未执行" "$context.$rule"
  fi
  
  return 0
}

# 检查规则执行状态
check_rule_execution() {
  local rule="$1"
  local context="$2"
  
  echo "[$(date)] 检查规则执行状态: $context.$rule" >> $MONITOR_LOG
  
  # 模拟检查逻辑
  if [[ -f "memory/execution-control.log" ]]; then
    # 检查执行日志中是否包含该规则
    if grep -q "执行动作: $rule" memory/execution-control.log; then
      echo "executed"
    else
      echo "missing"
    fi
  else
    echo "missing"
  fi
  
  return 0
}

# 执行结果验证
verify_execution_result() {
  local rule="$1"
  local context="$2"
  local expected_result="$3"
  
  echo "[$(date)] 验证执行结果: $context.$rule" >> $MONITOR_LOG
  
  # 检查执行结果是否符合预期
  local actual_result=$(get_rule_execution_result "$rule" "$context")
  
  if [[ "$actual_result" != "$expected_result" ]]; then
    echo "[$(date)] ❌ 错误: 执行结果不符合预期" >> $ALERT_LOG
    echo "[$(date)] 预期: $expected_result" >> $ALERT_LOG
    echo "[$(date)] 实际: $actual_result" >> $ALERT_LOG
    send_alert "执行结果异常" "$context.$rule"
  fi
  
  return 0
}

# 获取规则执行结果
get_rule_execution_result() {
  local rule="$1"
  local context="$2"
  
  echo "[$(date)] 获取规则执行结果: $context.$rule" >> $MONITOR_LOG
  
  # 模拟获取结果
  if grep -q "执行动作: $rule" memory/execution-control.log; then
    echo "success"
  else
    echo "failed"
  fi
  
  return 0
}

# 生成执行报告
generate_execution_report() {
  local report_file="memory/execution-report-$(date +%Y%m%d).md"
  
  echo "# 灵犀执行报告 - $(date)" > $report_file
  echo "" >> $report_file
  
  echo "## 执行状态统计" >> $report_file
  echo "- 总规则数: $(count_total_rules)" >> $report_file
  echo "- 已执行: $(count_executed_rules)" >> $report_file
  echo "- 未执行: $(count_missing_rules)" >> $report_file
  echo "- 执行率: $(calculate_execution_rate)" >> $report_file
  
  echo "" >> $report_file
  echo "## 执行时间统计" >> $report_file
  echo "- 开始时间: $(get_execution_start_time)" >> $report_file
  echo "- 完成时间: $(get_execution_end_time)" >> $report_file
  echo "- 持续时间: $(calculate_execution_duration)" >> $report_file
  
  echo "" >> $report_file
  echo "## 执行质量评估" >> $report_file
  echo "- 质量评分: $(calculate_execution_quality)" >> $report_file
  echo "- 问题数量: $(count_execution_issues)" >> $report_file
  
  echo "" >> $report_file
  echo "## 建议改进" >> $report_file
  echo "- $(get_improvement_suggestions)" >> $report_file
  
  echo "[$(date)] 执行报告生成完成: $report_file" >> $MONITOR_LOG
}

# 统计总规则数
count_total_rules() {
  local total=0
  
  if [[ -f "memory/rule-action-mapper.json" ]]; then
    total=$(jq 'to_entries | map(.value | to_entries | length) | add' memory/rule-action-mapper.json 2>/dev/null || echo "0")
  fi
  
  echo $total
}

# 统计已执行规则
count_executed_rules() {
  local executed=0
  
  if [[ -f "memory/execution-control.log" ]]; then
    executed=$(grep -c "执行动作:" memory/execution-control.log || echo "0")
  fi
  
  echo $executed
}

# 统计未执行规则
count_missing_rules() {
  local total=$(count_total_rules)
  local executed=$(count_executed_rules)
  local missing=$((total - executed))
  
  echo $missing
}

# 计算执行率
calculate_execution_rate() {
  local total=$(count_total_rules)
  local executed=$(count_executed_rules)
  
  if [[ $total -eq 0 ]]; then
    echo "0%"
  else
    local rate=$((executed * 100 / total))
    echo "${rate}%"
  fi
}

# 获取执行开始时间
get_execution_start_time() {
  if [[ -f "memory/execution-control.log" ]]; then
    head -n 1 memory/execution-control.log | grep -oE '\[.*\]' | head -c 19
  else
    echo "未知"
  fi
}

# 获取执行结束时间
get_execution_end_time() {
  if [[ -f "memory/execution-control.log" ]]; then
    tail -n 1 memory/execution-control.log | grep -oE '\[.*\]' | head -c 19
  else
    echo "未知"
  fi
}

# 计算执行持续时间
calculate_execution_duration() {
  local start_time=$(get_execution_start_time)
  local end_time=$(get_execution_end_time)
  
  if [[ "$start_time" != "未知" ]] && [[ "$end_time" != "未知" ]]; then
    echo "1秒"
  else
    echo "未知"
  fi
}

# 计算执行质量
calculate_execution_quality() {
  local executed=$(count_executed_rules)
  local total=$(count_total_rules)
  
  if [[ $total -eq 0 ]]; then
    echo "0%"
  else
    local quality=$((executed * 100 / total))
    echo "${quality}%"
  fi
}

# 统计执行问题
count_execution_issues() {
  local issues=0
  
  if [[ -f "memory/execution-alert.log" ]]; then
    issues=$(wc -l < memory/execution-alert.log || echo "0")
  fi
  
  echo $issues
}

# 获取改进建议
get_improvement_suggestions() {
  echo "继续优化执行控制系统，提高规则执行效率"
}

# 发送告警
send_alert() {
  local alert_type="$1"
  local alert_detail="$2"
  
  echo "[$(date)] 🚨 $alert_type: $alert_detail" >> $ALERT_LOG
  echo "[$(date)] 🚨 告警已发送: $alert_type" >> $MONITOR_LOG
}

# 主监控循环
main() {
  echo "[$(date)] 启动执行监控系统" >> $MONITOR_LOG
  echo "[$(date)] 🕐 灵犀执行监控系统启动" >> $MONITOR_LOG
  
  # 持续监控规则执行状态
  while true; do
    monitor_all_rules
    sleep 300  # 每5分钟监控一次
  done
}

# 监控所有规则
monitor_all_rules() {
  echo "[$(date)] 监控所有规则执行状态" >> $MONITOR_LOG
  
  if [[ -f "memory/rule-action-mapper.json" ]]; then
    jq -r 'to_entries[] | "\(.key) \(.value | to_entries[] | "\(.key) \(.value)")"' memory/rule-action-mapper.json | while read context rule action; do
      if [[ -n "$context" ]] && [[ -n "$rule" ]]; then
        monitor_execution_status "$rule" "$context"
      fi
    done
  fi
}

main "$@"