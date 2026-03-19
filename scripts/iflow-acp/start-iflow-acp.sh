#!/bin/bash
PORT=8081
     LOGFILE="/tmp/iflow-acp-$(date +%Y%m%d).log"

     echo "启动 iFlow ACP 服务器 (端口: $PORT)"
     iflow --experimental-acp --port $PORT >> $LOGFILE 2>&1

     # 检查状态
     if [ $? -eq 0 ]; then
         echo "服务器已启动，日志: $LOGFILE"
         echo "WebSocket 地址: ws://127.0.0.1:$PORT/acp"
     else
         echo "启动失败，查看日志: $LOGFILE"
     fi

