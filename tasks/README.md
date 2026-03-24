# 任务管理框架

## 📁 目录结构
```
tasks/
├── todo/          # 待办任务（简单列表）
├── doing/         # 正在任务（进度跟踪）
├── done/          # 已完成任务（详细记录）
├── task-cli.sh    # 任务管理命令行工具
└── README.md      # 本说明文件
```

## 🎯 任务状态定义

### 状态迁移
- **todo**: 待开始任务
- **doing**: 正在执行任务
- **done**: 已完成任务

### 状态转换
- `todo` → `doing`: 开始执行任务
- `doing` → `done`: 完成任务

## 📝 任务文件格式

### 待办任务 (todo/)
```markdown
# 任务名称

**状态**: todo  
**创建**: YYYY-MM-DD HH:MM  
**优先级**: high|medium|low  

## 任务描述
- [ ] 任务要求1
- [ ] 任务要求2
```

### 正在任务 (doing/)
```markdown
# 任务名称

**状态**: doing  
**创建**: YYYY-MM-DD HH:MM  
**进度**: XX%  

## 任务描述
- [x] 已完成步骤1
- [x] 已完成步骤2
- [ ] 正在执行步骤3
- [ ] 待执行步骤4

## 进度记录
- YYYY-MM-DD HH:MM 开始执行，进度 0%
- YYYY-MM-DD HH:MM 完成步骤1，进度 25%
```

### 已完成任务 (done/)
```markdown
# 任务名称

**状态**: done  
**创建**: YYYY-MM-DD HH:MM  
**完成**: YYYY-MM-DD HH:MM  
**耗时**: X小时Y分钟  

## 任务描述
- [x] 所有步骤已完成

## 交付成果
- [x] 交付物1
- [x] 交付物2

## 经验总结
- 技术收获：[简短描述]
- 工作方法：[简短描述]
- 改进方向：[简短描述]

## 相关文件
- 文件路径：[具体路径]
```

## 🛠️ 快速操作

### 使用命令行工具
```bash
# 显示帮助
./task-cli.sh help

# 创建任务
./task-cli.sh create "任务名称" [high|medium|low]

# 开始执行
./task-cli.sh start "任务名称"

# 完成任务
./task-cli.sh complete "任务名称"

# 取消任务
./task-cli.sh cancel "任务名称"

# 搜索任务
./task-cli.sh search "关键词"

# 列出任务
./task-cli.sh list [todo|doing|done|all]
```

### 手动操作（备用）
```bash
# 创建待办任务
echo "# 任务名称\n\n**状态**: todo\n**创建**: $(date '+%Y-%m-%d %H:%M')\n\n## 任务描述\n- [ ] 任务要求" > tasks/todo/任务名称.md

# 开始执行任务
mv tasks/todo/任务名称.md tasks/doing/

# 更新进度
# 编辑 doing/任务名称.md，更新进度和记录

# 完成任务
mv tasks/doing/任务名称.md tasks/done/
```

## 📋 任务看板

### 查看任务状态
```bash
# 简单的任务看板
echo "📋 任务看板 - $(date)"
echo "=================================="
echo "✅ 已完成 ($(ls tasks/done/*.md 2>/dev/null | wc -l)):"
ls tasks/done/*.md 2>/dev/null | while read f; do echo "  - $(basename "$f" .md)"; done
echo ""
echo "🔄 正在做 ($(ls tasks/doing/*.md 2>/dev/null | wc -l)):"
ls tasks/doing/*.md 2>/dev/null | while read f; do 
  name=$(basename "$f" .md)
  progress=$(grep "进度:" "$f" | cut -d: -f2 | tr -d ' %')
  echo "  - $name [$progress%]"
done
echo ""
echo "⏳ 待办 ($(ls tasks/todo/*.md 2>/dev/null | wc -l)):"
ls tasks/todo/*.md 2>/dev/null | while read f; do 
  name=$(basename "$f" .md)
  echo "  - $name"
done
```

## 🔄 维护规则

### 每日检查
- 检查 `todo/` 目录，安排任务优先级
- 检查 `doing/` 目录，更新任务进度
- 完成任务后移至 `done/` 目录

### 定期归档
- `done/` 目录中的任务按月归档
- 保留最近3个月的详细记录
- 更早的任务可简化或删除

### 灵活调整
- 任务格式可根据实际情况调整
- 操作流程可根据使用习惯优化
- 不必拘泥于固定格式，以实用为准

### 重要输出规则
- 遵循SOUL.md中的通用代码输出限制规则
- 任务管理中的代码输出同样需要遵循上述原则

---

**框架制定完成**  
**制定时间**: 2026-03-21 05:31  
**原则**: 简单、实用、灵活、高效

---

**框架制定完成**  
**制定时间**: 2026-03-21 05:31  
**原则**: 简单、实用、灵活、高效