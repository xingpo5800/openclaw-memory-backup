#!/bin/bash
# 任务管理命令行工具（简化版）

# 显示帮助信息
task-cli() {
  local cmd="$1"
  
  case "$cmd" in
    create)
      create_task "$2" "$3"
      ;;
    start)
      start_task "$2"
      ;;
    complete)
      complete_task "$2"
      ;;
    cancel)
      cancel_task "$2"
      ;;
    search)
      search_tasks "$2"
      ;;
    list)
      list_tasks "$2"
      ;;
    help|*)
      show_help
      ;;
  esac
}

# 显示帮助信息
show_help() {
  echo "🛠️ 任务管理工具"
  echo "=================================="
  echo "用法: task-cli <命令> [参数]"
  echo ""
  echo "命令:"
  echo "  create <任务名> [优先级]    - 创建新任务"
  echo "  start <任务名>             - 开始执行任务"
  echo "  complete <任务名>           - 完成任务"
  echo "  cancel <任务名>             - 取消任务"
  echo "  search <关键词>             - 搜索任务"
  echo "  list [状态]                - 列出任务"
  echo "  help                       - 显示帮助"
  echo ""
  echo "示例:"
  echo "  task-cli create '配置iFlow网关' high"
  echo "  task-cli start '配置iFlow网关'"
  echo "  task-cli search 'iFlow'"
  echo "=================================="
}

# 创建任务
create_task() {
  local task_name="$1"
  local priority="${2:-medium}"
  
  if [ -z "$task_name" ]; then
    echo "❌ 请提供任务名称"
    echo "用法: task-cli create <任务名> [优先级]"
    return 1
  fi
  
  local task_file="tasks/todo/$(date +%Y-%m-%d)_${task_name}.md"
  
  # 检查任务是否已存在
  if [ -f "$task_file" ] || [ -f "tasks/doing/$(date +%Y-%m-%d)_${task_name}.md" ] || [ -f "tasks/done/$(date +%Y-%m-%d)_${task_name}.md" ]; then
    echo "❌ 任务已存在: $task_name"
    return 1
  fi
  
  # 创建任务文件
  cat > "$task_file" << EOF
# $task_name

**状态**: todo  
**创建**: $(date '+%Y-%m-%d %H:%M')  
**优先级**: $priority  

## 任务描述
- [ ] 任务要求
EOF
  
  echo "✅ 任务已创建: $task_name"
}

# 开始执行任务
start_task() {
  local task_name="$1"
  
  if [ -z "$task_name" ]; then
    echo "❌ 请提供任务名称"
    echo "用法: task-cli start <任务名>"
    return 1
  fi
  
  local task_file="tasks/todo/$(date +%Y-%m-%d)_${task_name}.md"
  
  if [ ! -f "$task_file" ]; then
    echo "❌ 任务不存在: $task_name"
    return 1
  fi
  
  mv "$task_file" "tasks/doing/"
  
  # 更新任务状态为doing
  local doing_file="tasks/doing/$(date +%Y-%m-%d)_${task_name}.md"
  sed -i '' "s/状态: todo/状态: doing/" "$doing_file"
  sed -i '' "/创建:/a\\**进度**: 0%" "$doing_file"
  
  echo "✅ 任务已开始: $task_name"
}

# 完成任务
complete_task() {
  local task_name="$1"
  
  if [ -z "$task_name" ]; then
    echo "❌ 请提供任务名称"
    echo "用法: task-cli complete <任务名>"
    return 1
  fi
  
  local task_file="tasks/doing/$(date +%Y-%m-%d)_${task_name}.md"
  
  if [ ! -f "$task_file" ]; then
    echo "❌ 任务不存在或未开始: $task_name"
    return 1
  fi
  
  # 更新任务状态为done
  sed -i '' "s/状态: doing/状态: done/" "$task_file"
  sed -i '' "/创建:/a\\**完成**: $(date '+%Y-%m-%d %H:%M')" "$task_file"
  
  # 计算耗时
  local create_time=$(grep "创建:" "$task_file" | cut -d: -f2 | tr -d ' ')
  local create_timestamp=$(date -j -f "%Y-%m-%d %H:%M" "$create_time" +%s 2>/dev/null || echo "0")
  local current_timestamp=$(date +%s)
  local duration=$((current_timestamp - create_timestamp))
  local duration_minutes=$((duration / 60))
  local duration_hours=$((duration_minutes / 60))
  duration_minutes=$((duration_minutes % 60))
  
  sed -i '' "/完成:/a\\**耗时**: ${duration_hours}小时${duration_minutes}分钟" "$task_file"
  
  mv "$task_file" "tasks/done/"
  
  echo "✅ 任务已完成: $task_name"
  echo "   耗时: ${duration_hours}小时${duration_minutes}分钟"
}

# 取消任务
cancel_task() {
  local task_name="$1"
  
  if [ -z "$task_name" ]; then
    echo "❌ 请提供任务名称"
    echo "用法: task-cli cancel <任务名>"
    return 1
  fi
  
  local todo_file="tasks/todo/$(date +%Y-%m-%d)_${task_name}.md"
  local doing_file="tasks/doing/$(date +%Y-%m-%d)_${task_name}.md"
  
  if [ -f "$todo_file" ]; then
    rm "$todo_file"
    echo "✅ 任务已取消: $task_name"
  elif [ -f "$doing_file" ]; then
    rm "$doing_file"
    echo "✅ 任务已取消: $task_name"
  else
    echo "❌ 任务不存在: $task_name"
    return 1
  fi
}

# 搜索任务
search_tasks() {
  local keyword="$1"
  
  if [ -z "$keyword" ]; then
    echo "❌ 请提供搜索关键词"
    echo "用法: task-cli search <关键词>"
    return 1
  fi
  
  echo "🔍 搜索任务: '$keyword'"
  echo "=================================="
  
  # 搜索所有任务文件
  local found_tasks=()
  
  while IFS= read -r -d '' file; do
    if grep -q "$keyword" "$file"; then
      found_tasks+=("$file")
    fi
  done < <(find tasks/ -name "*.md" -print0)
  
  if [ ${#found_tasks[@]} -eq 0 ]; then
    echo "❌ 未找到相关任务"
    return 1
  fi
  
  for file in "${found_tasks[@]}"; do
    local task_name=$(basename "$file" .md | sed 's/^[0-9-]*_//')
    local status=$(grep "状态:" "$file" | cut -d: -f2 | tr -d ' ')
    local priority=$(grep "优先级:" "$file" | cut -d: -f2 | tr -d ' ')
    
    echo "📁 $task_name"
    echo "   状态: $status"
    echo "   优先级: $priority"
    echo "   文件: $file"
    echo ""
  done
}

# 列出任务
list_tasks() {
  local status="${1:-all}"
  
  echo "📋 任务列表 - $status"
  echo "=================================="
  
  case "$status" in
    todo)
      local count=$(ls tasks/todo/*.md 2>/dev/null | wc -l)
      echo "⏳ 待办任务 ($count):"
      if [ $count -gt 0 ]; then
        ls tasks/todo/*.md 2>/dev/null | while read f; do
          name=$(basename "$f" .md | sed 's/^[0-9-]*_//')
          priority=$(grep "优先级:" "$f" | cut -d: -f2 | tr -d ' ')
          echo "  - $name [$priority]"
        done
      else
        echo "  暂无待办任务"
      fi
      ;;
    doing)
      local count=$(ls tasks/doing/*.md 2>/dev/null | wc -l)
      echo "🔄 正在任务 ($count):"
      if [ $count -gt 0 ]; then
        ls tasks/doing/*.md 2>/dev/null | while read f; do
          name=$(basename "$f" .md | sed 's/^[0-9-]*_//')
          progress=$(grep "进度:" "$f" 2>/dev/null | cut -d: -f2 | tr -d ' %' || echo "N/A")
          echo "  - $name [$progress%]"
        done
      else
        echo "  暂无正在进行的任务"
      fi
      ;;
    done)
      local count=$(ls tasks/done/*.md 2>/dev/null | wc -l)
      echo "✅ 已完成任务 ($count):"
      if [ $count -gt 0 ]; then
        ls tasks/done/*.md 2>/dev/null | while read f; do
          name=$(basename "$f" .md | sed 's/^[0-9-]*_//')
          echo "  - $name"
        done
      else
        echo "  暂无已完成任务"
      fi
      ;;
    all)
      list_tasks "todo"
      echo ""
      list_tasks "doing"
      echo ""
      list_tasks "done"
      ;;
    *)
      echo "❌ 无效的状态: $status"
      echo "支持的状态: todo, doing, done, all"
      return 1
      ;;
  esac
}

# 如果直接运行此脚本，显示帮助
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
  task-cli "$@"
fi