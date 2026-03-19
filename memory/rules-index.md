# 规则索引

## 核心操作规则
- system-rules.md - 系统核心规则
- execution-optimization.md - 执行优化规则
- token-saver.md - 省tokens规则  
- execution-priority.md - 执行优先级规则
- communication.md - 通信规则
- animation-script.md - 动画脚本规则

## 规则加载优先级
1. 高优先级：system-rules.md (系统基础规则)
2. 高优先级：execution-optimization.md
3. 中优先级：token-saver.md, execution-priority.md
4. 低优先级：communication.md, animation-script.md

## 记忆更新规则
- 写入前先检查是否已有相关记忆
- 避免重复写入相同内容
- 重要操作前先确认