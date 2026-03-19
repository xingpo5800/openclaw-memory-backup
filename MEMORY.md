# 记忆索引

## 规则参考
- 文件组织规则：workspace/ORGANIZE.md (已更新)
- 工作区域规划：workspace/ORGANIZE.md (已更新)
- 规则索引：workspace/memory/rules-index.md

## 目录结构
当前工作区采用功能导向的目录结构，主要分为：
- projects/ : 项目管理 (workspace/projects/)
- knowledge/ : 知识管理 (workspace/knowledge/)
- tools/ : 工具配置 (workspace/tools/)
- memory/ : 记忆记录 (workspace/memory/)
  - YYYY-MM-DD.md : 每日记忆 (自动创建)
  - rules-index.md : 规则索引 (自动维护)
  - rules/: 规则文件 (workspace/rules/)
- rules/ : 规则管理 (workspace/rules/)
  - system-rules.md : 系统规则
  - token-saver.md : 省tokens规则
  - communication.md : 通信规则
  - animation-script.md : 动画脚本规则

## 记忆加载流程
1. AGENTS.md : 读取工作区配置
2. memory/rules-index.md : 读取规则索引
3. memory/YYYY-MM-DD.md : 读取今日记忆
4. 根据需要读取具体规则文件