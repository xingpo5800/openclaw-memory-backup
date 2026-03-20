# 系统插件能力说明

## 📋 插件概述
OpenClaw支持通过插件系统扩展功能，本文件说明当前已安装的插件及其能力。

## 🔌 已安装插件列表

### 飞书插件组
**来源**: `/Users/kevin/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw/extensions/feishu/`

#### feishu_doc - 飞书文档操作
**功能**: 飞书文档的读写操作
**注册工具**: feishu_doc, feishu_app_scopes
**使用场景**: 
- 文档内容获取和编辑
- 飞书文档管理
- 协作文档操作

#### feishu_chat - 飞书聊天
**功能**: 飞书聊天功能
**注册工具**: feishu_chat
**使用场景**: 飞书消息交互

#### feishu_wiki - 飞书知识库
**功能**: 飞书知识库操作
**注册工具**: feishu_wiki
**使用场景**: 知识库内容管理

#### feishu_drive - 飞书云盘
**功能**: 飞书云盘文件管理
**注册工具**: feishu_drive
**使用场景**: 云盘文件操作

#### feishu_bitable - 飞书多维表格
**功能**: 飞书多维表格操作
**注册工具**: bitable相关工具
**使用场景**: 表格数据处理

## ⚙️ 插件配置状态

### 当前配置
```json
{
  "plugins.allow": "空（未明确设置）",
  "发现插件": "feishu插件组",
  "状态": "插件已注册，但需要明确信任配置"
}
```

### 配置建议
**文件位置**: OpenClaw配置文件
**配置项**: `plugins.allow`
**建议值**: 明确列出信任的插件ID，如 `["feishu"]`

## 🚀 插件使用方法

### 飞书文档操作
```bash
# 查看飞书文档
feishu_doc <document_id>

# 编辑飞书文档
feishu_doc <document_id> --edit
```

### 飞书云盘操作
```bash
# 列出云盘文件
feishu_drive list

# 上传文件到云盘
feishu_drive upload <file_path>
```

### 飞书知识库操作
```bash
# 查看知识库
feishu_wiki <wiki_id>

# 管理知识条目
feishu_wiki <wiki_id> manage
```

## 🔧 插件管理

### 查看插件状态
```bash
openclaw extensions list
```

### 检查插件配置
```bash
# 查看当前插件配置
cat ~/.openclaw/config.json | grep plugins
```

### 更新插件
```bash
# 更新OpenClaw（包含插件）
openclaw update

# 或者重新安装插件
npm install -g openclaw
```

## ⚠️ 注意事项

### 安全性
- 插件具有系统访问权限
- 确保插件来源可信
- 定期检查插件更新

### 性能影响
- 插件可能增加启动时间
- 部分插件可能在后台运行
- 不使用的插件可以禁用

### 兼容性
- 插件版本与OpenClaw版本兼容
- 定期更新以保持兼容性
- 检查插件的依赖关系

## 📈 插件扩展

### 添加新插件
1. 确认插件来源可信
2. 检查插件兼容性
3. 在配置中添加信任
4. 重启OpenClaw加载插件

### 自定义插件
- 参考OpenClaw插件开发文档
- 遵循插件开发规范
- 提交插件到官方仓库

## 🔄 更新日志

### 最近更新
- **日期**: 2026-03-20
- **更新内容**: 安装并配置feishu插件组
- **状态**: 插件已注册，等待信任配置

### 计划更新
- 定期检查插件更新
- 优化插件配置
- 添加更多功能插件

---

**文档维护**: 定期更新插件状态和能力说明
**最后更新**: 2026-03-20