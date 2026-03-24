#!/bin/bash
# 任务看板脚本

echo "📋 任务看板 - $(date '+%Y-%m-%d %H:%M')"
echo "=================================="

# 统计各状态任务数量
todo_count=$(ls tasks/todo/*.md 2>/dev/null | wc -l)
doing_count=$(ls tasks/doing/*.md 2>/dev/null | wc -l)
done_count=$(ls tasks/done/*.md 2>/dev/null | wc -l)

echo "✅ 已完成 ($done_count):"
if [ $done_count -gt 0 ]; then
    ls tasks/done/*.md 2>/dev/null | while read f; do
        name=$(basename "$f" .md)
        echo "  - $name"
    done
else
    echo "  暂无已完成任务"
fi

echo ""
echo "🔄 正在做 ($doing_count):"
if [ $doing_count -gt 0 ]; then
    ls tasks/doing/*.md 2>/dev/null | while read f; do
        name=$(basename "$f" .md)
        # 提取进度信息
        progress=$(grep "进度:" "$f" 2>/dev/null | cut -d: -f2 | tr -d ' %' || echo "N/A")
        echo "  - $name [$progress%]"
    done
else
    echo "  暂无正在进行的任务"
fi

echo ""
echo "⏳ 待办 ($todo_count):"
if [ $todo_count -gt 0 ]; then
    ls tasks/todo/*.md 2>/dev/null | while read f; do
        name=$(basename "$f" .md)
        # 提取优先级信息
        priority=$(grep "优先级:" "$f" 2>/dev/null | cut -d: -f2 | tr -d ' ' || echo "medium")
        echo "  - $name [$priority]"
    done
else
    echo "  暂无待办任务"
fi

echo ""
echo "=================================="
echo "💡 操作提示:"
echo "  创建任务: echo \"# 任务名\" > tasks/todo/任务名.md"
echo "  开始执行: mv tasks/todo/任务名.md tasks/doing/"
echo "  完成任务: mv tasks/doing/任务名.md tasks/done/"
echo "=================================="