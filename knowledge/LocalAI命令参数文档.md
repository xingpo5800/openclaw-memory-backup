# LocalAI 中文命令参数完整文档

## 🎯 项目概述

LocalAI 是一个免费的、开源的 OpenAI 替代方案，可以作为 OpenAI API 的本地替代品，支持多种模型和硬件加速。

## 🚀 快速开始

### 基本安装和启动

#### macOS
```bash
# 下载 DMG 文件
curl -fsSL https://github.com/mudler/LocalAI/releases/latest/download/LocalAI.dmg -o LocalAI.dmg

# 安装 DMG 后，在终端运行以下命令解除隔离
sudo xattr -d com.apple.quarantine /Applications/LocalAI.app
```

#### Docker 运行
```bash
# CPU 版本
docker run -ti --name local-ai -p 8080:8080 localai/localai:latest

# 如果已有容器，重新启动
docker start -i local-ai
```

### GPU 版本

#### NVIDIA GPU
```bash
# CUDA 13.0
docker run -ti --name local-ai -p 8080:8080 --gpus all localai/localai:latest-gpu-nvidia-cuda-13

# CUDA 12.0
docker run -ti --name local-ai -p 8080:8080 --gpus all localai/localai:latest-gpu-nvidia-cuda-12

# NVIDIA Jetson (L4T ARM64) - CUDA 12
docker run -ti --name local-ai -p 8080:8080 --gpus all localai/localai:latest-nvidia-l4t-arm64

# NVIDIA Jetson (L4T ARM64) - CUDA 13
docker run -ti --name local-ai -p 8080:8080 --gpus all localai/localai:latest-nvidia-l4t-arm64-cuda-13
```

#### AMD GPU (ROCm)
```bash
docker run -ti --name local-ai -p 8080:8080 --device=/dev/kfd --device=/dev/dri --group-add=video localai/localai:latest-gpu-hipblas
```

#### Intel GPU (oneAPI)
```bash
docker run -ti --name local-ai -p 8080:8080 --device=/dev/dri/card1 --device=/dev/dri/renderD128 localai/localai:latest-gpu-intel
```

#### Vulkan GPU
```bash
docker run -ti --name local-ai -p 8080:8080 localai/localai:latest-gpu-vulkan
```

## 📦 模型管理

### 运行模型

#### 从模型库运行
```bash
# 查看可用模型
local-ai models list

# 从模型库运行模型
local-ai run llama-3.2-1b-instruct:q4_k_m

# 或在 Web UI 的模型选项卡中选择，访问 https://models.localai.io
```

#### 从 HuggingFace 运行
```bash
# 直接从 HuggingFace 运行模型
local-ai run huggingface://TheBloke/phi-2-GGUF/phi-2.Q8_0.gguf
```

#### 从 Ollama Registry 运行
```bash
# 从 Ollama OCI registry 安装并运行模型
local-ai run ollama://gemma:2b
```

#### 从配置文件运行
```bash
# 从 YAML 配置文件运行模型
local-ai run https://gist.githubusercontent.com/用户名/.../phi-2.yaml
```

#### 从 OCI Registry 运行
```bash
# 从标准 OCI registry (如 Docker Hub) 运行模型
local-ai run oci://localai/phi-2:latest
```

### 模型管理命令

#### 查看已安装模型
```bash
local-ai models list
```

#### 删除模型
```bash
local-ai models remove 模型名称
```

#### 模型信息
```bash
local-ai models info 模型名称
```

## ⚙️ 命令行参数详解

### 基本命令格式
```bash
local-ai [选项] <命令> [参数]
```

### 主要选项

#### 1. 模型运行选项
```bash
# 运行特定模型
local-ai run 模型名称

# 指定配置文件
local-ai --config /path/to/config.yaml run 模型名称

# 指定模型目录
local-ai --models-path /path/to/models run 模型名称

# 指定端口
local-ai --port 8080 run 模型名称
```

#### 2. 系统选项
```bash
# 查看版本
local-ai --version

# 查看帮助
local-ai --help

# 详细输出
local-ai --verbose run 模型名称

# 调试模式
local-ai --debug run 模型名称
```

#### 3. 配置管理选项
```bash
# 显示当前配置
local-ai config show

# 验证配置文件
local-ai config validate /path/to/config.yaml

# 编辑配置
local-ai config edit

# 备份配置
local-ai config backup /path/to/backup.yaml
```

### 高级选项

#### 1. 资源管理
```bash
# 限制内存使用
local-ai --memory-limit 8G run 模型名称

# 限制 GPU 内存
local-ai --gpu-memory-limit 4G run 模型名称

# 限制并发请求数
local-ai --max-concurrent 5 run 模型名称

# 限制请求超时
local-ai --timeout 300 run 模型名称
```

#### 2. 网络配置
```bash
# 绑定地址
local-ai --host 0.0.0.0 run 模型名称

# 绑定端口
local-ai --port 8080 run 模型名称

# 启用 CORS
local-ai --enable-cors run 模型名称

# 设置 API 密钥
local-ai --api-key your-api-key run 模型名称
```

#### 3. 日志和监控
```bash
# 启用日志
local-ai --log-level info run 模型名称

# 日志文件路径
local-ai --log-file /path/to/localai.log run 模型名称

# 启用性能监控
local-ai --enable-monitoring run 模型名称

# 启用 Prometheus 指标
local-ai --enable-metrics run 模型名称
```

## 🎨 Web UI 使用

### 启动 Web UI
```bash
# 启动带 Web UI 的 LocalAI
docker run -p 8080:8080 --name local-ai -v /path/to/models:/models -ti localai/localai:latest

# 访问 Web UI
# http://localhost:8080
```

### Web UI 功能
- **模型管理**: 浏览、安装、删除模型
- **聊天界面**: 与 AI 模型对话
- **图像生成**: 创建图像
- **音频处理**: 语音识别和合成
- **设置配置**: 修改 LocalAI 设置

## 🔌 API 使用

### 基础 API 端点

#### Chat Completions
```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "llama-3.2-1b-instruct",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

#### Image Generation
```bash
curl http://localhost:8080/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "stable-diffusion",
    "prompt": "A beautiful landscape",
    "size": "512x512",
    "n": 1
  }'
```

#### Audio Transcription
```bash
curl http://localhost:8080/v1/audio/transcriptions \
  -F "file=@audio.wav" \
  -F "model=whisper" \
  -F "language=en"
```

#### Text to Speech
```bash
curl http://localhost:8080/v1/audio/speech \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "tts-1",
    "input": "Hello, this is a test.",
    "voice": "alloy",
    "response_format": "mp3"
  }' \
  --output speech.mp3
```

### 高级 API 功能

#### Function Calling
```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "llama-3.2-1b-instruct",
    "messages": [
      {"role": "user", "content": "What is the weather in Tokyo?"}
    ],
    "functions": [
      {
        "name": "get_weather",
        "description": "Get the current weather for a location",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string",
              "description": "The city and state, e.g. San Francisco, CA"
            }
          },
          "required": ["location"]
        }
      }
    ]
  }'
```

#### Vision API
```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "llava",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "What is in this image?"},
          {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
        ]
      }
    ]
  }'
```

#### Real-time API
```bash
# WebSocket 实时对话
wscat -c ws://localhost:8080/v1/chat/completions

# 发送消息
{
  "model": "llama-3.2-1b-instruct",
  "messages": [{"role": "user", "content": "Hello!"}],
  "stream": true
}
```

## 📋 配置文件详解

### 基本配置文件格式
```yaml
# localai.yaml
models:
  - name: llama-3.2-1b-instruct
    path: /models/llama-3.2-1b-instruct.Q4_K_M.gguf
  
  - name: stable-diffusion
    parameters:
      model: /models/stable-diffusion-v1.5
      enable_attention_slicing: true

backend: llama.cpp

parameters:
  temperature: 0.7
  max_tokens: 1000
  top_p: 0.9

server:
  host: 0.0.0.0
  port: 8080
  enable_cors: true

logging:
  level: info
  file: /var/log/localai.log
```

### 高级配置选项

#### 后端配置
```yaml
backends:
  llama.cpp:
    parameters:
      n_ctx: 4096
      n_gpu_layers: 35
      n_threads: 4
      
  transformers:
    parameters:
      device: cuda
      torch_dtype: float16

  diffusers:
    parameters:
      scheduler: euler_a
      enable_xformers_memory_efficient_attention: true
```

#### 模型特定配置
```yaml
models:
  - name: chat-model
    backend: llama.cpp
    parameters:
      temperature: 0.8
      top_p: 0.9
      repeat_penalty: 1.1
      
  - name: image-model
    backend: diffusers
    parameters:
      height: 512
      width: 512
      guidance_scale: 7.5
      
  - name: audio-model
    backend: whisper
    parameters:
      language: auto
      task: transcribe
```

## 🛠️ 后端管理

### 后端列表

#### 文本生成后端
- **llama.cpp**: 高效的 LLM 推理，支持 CPU/GPU
- **vLLM**: 快速的 LLM 推理，使用 PagedAttention
- **transformers**: HuggingFace transformers 框架
- **MLX**: Apple Silicon 优化
- **MLX-VLM**: Apple Silicon 视觉-语言模型

#### 音频处理后端
- **whisper.cpp**: OpenAI Whisper 的 C++ 实现
- **faster-whisper**: 快速的 Whisper 识别
- **moonshine**: 超快转录引擎
- **coqui**: 1100+ 语言的 TTS
- **piper**: 快速神经网络 TTS 系统

#### 图像生成后端
- **stablediffusion.cpp**: Stable Diffusion 的 C++ 实现
- **diffusers**: HuggingFace 扩散模型

### 后端管理命令

#### 安装后端
```bash
# 从后端库安装后端
local-ai backend install llama.cpp

# 从 URL 安装后端
local-ai backend install https://github.com/用户名/后端.git

# 查看可用后端
local-ai backend list
```

#### 后端配置
```bash
# 查看后端配置
local-ai backend config llama.cpp

# 更新后端配置
local-ai backend update llama.cpp --parameter n_ctx=8192

# 删除后端
local-ai backend remove llama.cpp
```

## 🎯 实际应用示例

### 1. 聊天机器人
```bash
# 启动 LocalAI
docker run -p 8080:8080 --name local-ai -v /models:/models localai/localai:latest

# 测试聊天
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.2-1b-instruct",
    "messages": [
      {"role": "user", "content": "你好，我想了解人工智能"}
    ]
  }'
```

### 2. 图像生成
```bash
# 生成图像
curl -X POST http://localhost:8080/v1/images/generations \
  -H "Content-Type: application/json" \
  -d '{
    "model": "stable-diffusion",
    "prompt": "一只可爱的猫在花园里玩耍",
    "size": "512x512"
  }'
```

### 3. 语音转文字
```bash
# 语音识别
curl -X POST http://localhost:8080/v1/audio/transcriptions \
  -F "file=@audio.wav" \
  -F "model=whisper"
```

### 4. 文字转语音
```bash
# 语音合成
curl -X POST http://localhost:8080/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "你好，世界！",
    "voice": "nova"
  }' \
  --output chinese_speech.mp3
```

## 🔧 故障排除

### 常见问题

#### 1. 模型加载失败
```bash
# 检查模型文件
ls -la /models/

# 检查模型格式
file /models/模型文件.gguf

# 重新下载模型
local-ai run 重新下载模型名称
```

#### 2. GPU 加速问题
```bash
# 检查 GPU 支持
nvidia-smi  # NVIDIA
rocm-smi    # AMD

# 检查 LocalAI GPU 支持
docker run --gpus all localai/localai:latest-gpu-nvidia-cuda-13 --help
```

#### 3. 端口冲突
```bash
# 检查端口占用
lsof -i :8080

# 使用不同端口
docker run -p 8081:8080 localai/localai:latest
```

#### 4. 内存不足
```bash
# 检查系统内存
free -h

# 使用量化模型
local-ai run llama-3.2-1b-instruct:q4_k_m

# 限制内存使用
local-ai --memory-limit 4G run 模型名称
```

### 日志和调试

#### 启用详细日志
```bash
# 详细模式
local-ai --verbose run 模型名称

# 调试模式
local-ai --debug run 模型名称

# 查看日志
tail -f /var/log/localai.log
```

#### 性能监控
```bash
# 启用监控
local-ai --enable-monitoring run 模型名称

# 查看 metrics
curl http://localhost:8080/metrics
```

## 📚 更多资源

### 官方文档
- [官方文档](https://localai.io/)
- [快速开始指南](https://localai.io/basics/getting_started/)
- [功能特性](https://localai.io/features/)
- [API 文档](https://localai.io/api/)

### 社区资源
- [Discord 社区](https://discord.gg/uJAaKSAGDy)
- [GitHub 讨论](https://github.com/go-skynet/LocalAI/discussions)
- [示例仓库](https://github.com/mudler/LocalAI-examples)
- [模型库](https://models.localai.io)

### 相关项目
- [LocalAGI](https://github.com/mudler/LocalAGI) - AI Agent 平台
- [LocalRecall](https://github.com/mudler/LocalRecall) - 记忆系统
- [WebUI 界面](https://github.com/Jirubizu/localai-admin)

---

**文档版本**: v1.0  
**创建时间**: 2026-03-20  
**创建者**: 灵犀 AI 助手  
**数据来源**: LocalAI 官方文档和 GitHub 仓库