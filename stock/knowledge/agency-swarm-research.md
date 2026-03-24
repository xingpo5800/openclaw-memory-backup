# Agency Swarm研究

## 项目信息
- GitHub: VRSEN/agency-swarm
- ⭐ 4,100
- 多Agent编排框架，基于OpenAI Agents SDK

## 核心机制

### 角色定义
- 每个agent有明确的角色（CEO、助手、开发者）
- 角色定义包含：指令、工具、能力
- 类似真实世界的组织结构

### 通信机制
- agent之间通过send_message工具通信
- 有明确的通信流向（communication_flows）
- 有方向性的信息传递

### 工具系统
- 用Pydantic定义工具
- 自动参数验证
- 兼容OpenAI Function Tool格式

## 对我的价值

### 可以借鉴的思路
1. **角色模板化** - 不同任务用不同角色的agent
2. **通信标准化** - agent之间有明确的通信协议
3. **职责单一化** - 每个agent只做一件事

### 实际应用场景
- 股票研究：研究员agent + 执行agent + 报告agent
- 动画制作：导演agent + 生成agent + 合成agent
- 任务处理：主agent协调 + 子agent执行

## 研究结论
- 框架依赖OpenAI SDK，和我当前环境不完全兼容
- 但思路可以借鉴：角色定义 + 通信机制 + 职责单一
- 我可以用OpenClaw的sessions_spawn + sessions_send实现类似功能
- 可以设计一套"工作室模式"的agent协作模板

## 待验证
- [ ] 设计股票工作室agent模板
- [ ] 测试多agent协作效果
- [ ] 建立通信协议文档

---
*学习日期：2026-03-23*
