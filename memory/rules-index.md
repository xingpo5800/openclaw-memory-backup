# 规则索引

## 核心原则

**不被调用的规则是无效规则。**

## 规则层级

| 层级 | 规则 | 说明 |
|------|------|------|
| 最高 | 核心规则.md | 不可违背的底线 |
| 高 | 审查规则.md | 保证规则健康 |
| 中 | system-rules.md | 执行原则+自检 |
| 低 | 各专项规则 | 具体工具规则 |

## 索引状态（2026-03-22全面审查后）

### 核心基石 ✅
- 核心规则.md - 不伤害人类+立场边界 | 始终生效
- 审查规则.md - 规则健康审查+调用审查 | 规则修改时触发，禁止任务执行时调用
- 备份规则.md - 定时备份机制 | 定时任务触发
- session-rules.md - Session管理闭环 | session开始/结束时触发

### 执行原则 ✅
- system-rules.md - 执行原则+自检机制 | session开始时触发
- execution-standards.md - 执行流程 | 任务执行时触发
- execution-priority.md - 进化价值判断 | 任务优先级时触发
- execution-optimization.md - 优化目标 | 遇到优化需求时触发
- 执行感知.md - 自我感知+精准诊断 | 执行中/后触发

### 工作流程 ✅
- workflow.md - 规则触发流程 | 工作流程时触发
- rule-creation.md - 规则创建原则 | 创建规则时触发
- rule-execution-checklist.md - 自检清单 | 毅哥要求/定期自检

### 工具规则 ✅
- token-saver.md - 省Token习惯 | 始终生效
- token-efficient-execution.md - 高效加载习惯 | 始终生效
- task-management.md - 任务管理 | 任务管理时触发
- files-manager.md - 已删除，内容并入token-saver.md
- animation-script.md - 动画剧本规则 | 动画剧本时触发

## 记忆调用原则

- 今日记忆始终加载
- 专项经验按需调用
- 不全加载，按需搜索

## 专项经验文件

- memory/pixverse-cli-experience.md - PixVerse CLI经验
