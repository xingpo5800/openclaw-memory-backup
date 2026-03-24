# PixVerse CLI 经验

## CLI工具（核心成果）

通过31次迭代（pixverse_v1.py → v31.py），构建了完整的PixVerse CLI工具。

- **npm包**：`pixverse`，版本1.0.3
- **安装**：`npm install -g pixverse`
- **认证**：`pixverse auth login`
- **使用**：`pixverse create video --prompt "描述"`
- **版本**：`pixverse --version`

### CLI功能
- OAuth Device Code认证流程
- SSH隧道代理支持（SOCKS5 1080端口）
- 视频生成（--model, --duration, --quality, --aspect-ratio）
- 账号信息查询
- JSON输出支持

## 认证流程

### SSH隧道代理方案
- 命令：`ssh -i ~/.ssh/sshto18 -p 2288 -D 1080 -f -N kevin@study.luckyfamily.top`
- 端口：1080（SOCKS5）
- VPS：study.luckyfamily.top

### 认证关键
- PixVerse使用OAuth Device Code流程
- CLI命令：`pixverse auth login`
- CLI走代理才能正常轮询token

## 积分规则
- Free账号150积分开始
- HD质量（720p）消耗积分多
- 360p/480p消耗少但质量差
- 积分用完需等重置或购买

## 重要教训

**必须写经验总结。** 做完重要任务后立即写，不写就忘，下次从零开始。

---
*更新时间：2026-03-22*
