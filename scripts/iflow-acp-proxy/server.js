const express = require('express');
const WebSocket = require('ws');
const { v4: uuidv4 } = require('uuid');

// 创建 Express 应用和 HTTP 服务器
const app = express();
app.use(express.json({ limit: '10mb' }));

// 用于存储等待响应的 Promise 的 Map
const pendingRequests = new Map();

// 创建 WebSocket 客户端连接到 iFlow ACP 服务器
let acpWs = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

function connectToACP() {
  console.log('🔄 连接到 iFlow ACP 服务器...');
  
  acpWs = new WebSocket('ws://127.0.0.1:8081/acp');
  
  acpWs.on('open', () => {
    console.log('✅ 成功连接到 iFlow ACP 服务器');
    reconnectAttempts = 0; // 重置重连计数
  });
  
  acpWs.on('message', (data) => {
    const messageStr = data.toString();
    console.log('📥 收到原始 ACP 消息:', messageStr.substring(0, 100) + (messageStr.length > 100 ? '...' : ''));
    
    // 检查是否为注释或非 JSON 消息
    if (messageStr.startsWith('//')) {
      // 这可能是 ACP 的某种状态消息或注释
      console.log('💬 ACP 状态消息:', messageStr);
      return;
    }
    
    try {
      const message = JSON.parse(messageStr);
      console.log('📥 解析后的 ACP 消息:', message.type || message.id || 'unknown');
      
      // 检查是否为响应消息
      if (message.id) {
        const requestResolver = pendingRequests.get(message.id);
        if (requestResolver) {
          // 解析请求，移除处理器
          requestResolver.resolve(message);
          pendingRequests.delete(message.id);
        }
      } else if (message.type) {
        // 检查是否为某种类型的响应
        console.log('🔍 检查消息类型:', message.type);
      }
    } catch (error) {
      console.error('处理 ACP 消息错误:', error.message, '原始数据:', messageStr);
    }
  });
  
  acpWs.on('error', (error) => {
    console.error('ACP 连接错误:', error.message);
  });
  
  acpWs.on('close', () => {
    console.log('ACP 连接关闭，尝试重连...');
    
    // 拒绝所有待处理的请求
    for (const [id, resolver] of pendingRequests) {
      resolver.reject(new Error('ACP 连接断开'));
      pendingRequests.delete(id);
    }
    
    // 尝试重连
    if (reconnectAttempts < maxReconnectAttempts) {
      reconnectAttempts++;
      console.log(`重连尝试 ${reconnectAttempts}/${maxReconnectAttempts}`);
      setTimeout(connectToACP, 2000 * reconnectAttempts); // 指数退避
    } else {
      console.error('达到最大重连次数，停止重连');
    }
  });
}

// 初始化连接
connectToACP();

// 检查 ACP 连接状态
function isACPConnected() {
  return acpWs && acpWs.readyState === WebSocket.OPEN;
}

// 健康检查端点
app.get('/health', (req, res) => {
  res.json({
    status: isACPConnected() ? 'healthy' : 'unhealthy',
    acp_connected: isACPConnected(),
    timestamp: new Date().toISOString()
  });
});

// 模型列表端点
app.get('/v1/models', (req, res) => {
  // 返回支持的模型列表
  res.json({
    object: 'list',
    data: [
      { id: 'qwen3-coder-plus', object: 'model', created: 1769396866, owned_by: 'iflow' },
      { id: 'kimi-k2', object: 'model', created: 1769149523, owned_by: 'iflow' },
      { id: 'deepseek-v3.2', object: 'model', created: 1769412182, owned_by: 'iflow' },
      { id: 'qwen3-max', object: 'model', created: 1769411489, owned_by: 'iflow' },
      { id: 'kimi-k2-0905', object: 'model', created: 1769411073, owned_by: 'iflow' }
    ]
  });
});

// 聊天完成端点
app.post('/v1/chat/completions', async (req, res) => {
  if (!isACPConnected()) {
    return res.status(503).json({
      error: {
        type: 'service_unavailable',
        message: 'ACP 服务器未连接'
      }
    });
  }
  
  const requestId = uuidv4();
  console.log(`📥 收到聊天请求 [${requestId}]: ${req.body.model}`);
  
  try {
    // 创建一个 Promise 来处理响应
    const responsePromise = new Promise((resolve, reject) => {
      pendingRequests.set(requestId, { resolve, reject });
      
      // 设置超时
      setTimeout(() => {
        if (pendingRequests.has(requestId)) {
          pendingRequests.delete(requestId);
          reject(new Error('请求超时'));
        }
      }, 60000); // 60秒超时
    });
    
    // 构建 ACP 请求消息
    // 基于错误日志，尝试直接发送消息内容，让 iFlow 内部处理
    // 可能 iFlow ACP 期望的是直接的消息内容而不是 RPC 调用
    const acpRequest = {
      type: 'message',
      id: requestId,
      content: req.body.messages[req.body.messages.length - 1].content, // 获取用户消息
      model: req.body.model,
      options: {
        temperature: req.body.temperature || 0.7,
        max_tokens: req.body.max_tokens || 1000,
      }
    };
    
    // 发送请求到 ACP 服务器
    acpWs.send(JSON.stringify(acpRequest));
    
    // 等待响应
    const acpResponse = await responsePromise;
    console.log(`📤 收到 ACP 响应 [${requestId}]:`, acpResponse);
    
    // 转换 ACP 响应为 OpenAI 格式
    const openAIResponse = {
      id: `chat-${uuidv4()}`,
      object: 'chat.completion',
      created: Math.floor(Date.now() / 1000),
      model: req.body.model,
      choices: [{
        index: 0,
        message: {
          role: 'assistant',
          content: acpResponse.content || acpResponse.result || JSON.stringify(acpResponse)
        },
        finish_reason: 'stop'
      }],
      usage: {
        prompt_tokens: 0, // ACP 可能不提供这些信息
        completion_tokens: 0,
        total_tokens: 0
      }
    };
    
    res.json(openAIResponse);
  } catch (error) {
    console.error(`请求 [${requestId}] 处理错误:`, error);
    
    // 从待处理请求中移除
    if (pendingRequests.has(requestId)) {
      pendingRequests.delete(requestId);
    }
    
    res.status(500).json({
      error: {
        type: 'upstream_error',
        message: error.message
      }
    });
  }
});

const PORT = 8082;
const server = app.listen(PORT, '127.0.0.1', () => {
  console.log(`🚀 ACP to OpenAI 代理服务器启动在 http://127.0.0.1:${PORT}`);
  console.log('🔍 检查 ACP 服务器连接状态...');
});

// 优雅关闭
process.on('SIGTERM', () => {
  console.log('正在关闭服务器...');
  server.close(() => {
    console.log('服务器已关闭');
  });
});

module.exports = app;