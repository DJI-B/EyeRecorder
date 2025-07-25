"""
WebSocket连接管理模块
管理与设备的WebSocket连接和图像数据接收
"""

import json
import logging
import asyncio
import threading
import time
from typing import Optional, List
import cv2
import numpy as np
import websockets
from PyQt5.QtCore import QObject, pyqtSignal


class WebSocketManager(QObject):
    """
    WebSocket连接管理器
    负责管理与设备的连接、重连和数据接收
    """
    
    # 定义信号
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    error_occurred = pyqtSignal(str)
    image_received = pyqtSignal(np.ndarray)  # 发送图像数据
    status_updated = pyqtSignal(str)  # 状态更新
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.url = ""
        self.websocket = None
        self.is_connected_flag = False
        self.is_running = False
        self.current_image = None
        self.connection_thread = None
        self.url_variants = []  # URL变体列表
        self.current_url_index = 0  # 当前尝试的URL索引
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
        # 图像接收计数
        self.image_count = 0
        self.last_image_time = 0
        
        # 重连参数
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 3  # 秒
    
    def set_url(self, url: str):
        """设置WebSocket URL"""
        self.url = url.strip()
        self._generate_url_variants()
    
    def _generate_url_variants(self):
        """生成URL变体列表用于重连尝试"""
        if not self.url:
            return
            
        base_url = self.url.replace('ws://', '').replace('wss://', '')
        
        # 生成不同的URL变体
        self.url_variants = [
            f"ws://{base_url}",
            f"wss://{base_url}"
        ]
        
        # 如果没有端口，尝试常见端口
        if ':' not in base_url:
            self.url_variants.extend([
                f"ws://{base_url}:8080",
                f"ws://{base_url}:3000",
                f"wss://{base_url}:8080",
                f"wss://{base_url}:3000"
            ])
    
    def connect(self):
        """连接到WebSocket服务器"""
        if self.is_running:
            self.disconnect()
            
        if not self.url:
            self.error_occurred.emit("请设置有效的WebSocket URL")
            return
        
        self.is_running = True
        self.reconnect_attempts = 0
        self.current_url_index = 0
        
        # 在新线程中启动连接
        self.connection_thread = threading.Thread(target=self._run_connection)
        self.connection_thread.daemon = True
        self.connection_thread.start()
        
        self.status_updated.emit("正在连接...")
    
    def disconnect(self):
        """断开WebSocket连接"""
        self.is_running = False
        
        if self.websocket:
            try:
                asyncio.create_task(self.websocket.close())
            except:
                pass
            self.websocket = None
        
        self.is_connected_flag = False
        self.current_image = None
        self.status_updated.emit("已断开连接")
        self.disconnected.emit()
    
    def is_connected(self):
        """检查是否已连接"""
        return self.is_connected_flag and self.websocket is not None
    
    def get_current_image(self):
        """获取当前图像"""
        return self.current_image
    
    def _run_connection(self):
        """在新线程中运行连接"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._connection_loop())
        except Exception as e:
            self.logger.error(f"WebSocket连接线程错误: {e}")
            self.error_occurred.emit(f"连接错误: {e}")
        finally:
            loop.close()
    
    async def _connection_loop(self):
        """连接循环"""
        while self.is_running:
            try:
                current_url = self._get_current_url()
                if not current_url:
                    self.error_occurred.emit("所有URL尝试失败")
                    break
                
                self.status_updated.emit(f"尝试连接: {current_url}")
                
                async with websockets.connect(
                    current_url,
                    max_size=None,
                    max_queue=None
                ) as websocket:
                    self.websocket = websocket
                    self.is_connected_flag = True
                    self.reconnect_attempts = 0
                    
                    self.status_updated.emit("连接成功")
                    self.connected.emit()
                    
                    # 监听消息
                    await self._listen_for_messages()
                    
            except websockets.exceptions.ConnectionClosed:
                self.logger.info("WebSocket连接已关闭")
                break
            except Exception as e:
                self.logger.error(f"WebSocket连接错误: {e}")
                self._handle_connection_error()
                
            finally:
                self.is_connected_flag = False
                self.websocket = None
                
            # 如果需要重连
            if self.is_running and self._should_reconnect():
                await asyncio.sleep(self.reconnect_delay)
            else:
                break
    
    def _get_current_url(self):
        """获取当前URL"""
        if not self.url_variants:
            return self.url
            
        if self.current_url_index < len(self.url_variants):
            return self.url_variants[self.current_url_index]
        return None
    
    def _handle_connection_error(self):
        """处理连接错误"""
        self.current_url_index += 1
        if self.current_url_index >= len(self.url_variants):
            self.current_url_index = 0
            self.reconnect_attempts += 1
    
    def _should_reconnect(self):
        """判断是否应该重连"""
        return (self.is_running and 
                self.reconnect_attempts < self.max_reconnect_attempts)
    
    async def _listen_for_messages(self):
        """监听消息"""
        try:
            async for message in self.websocket:
                if not self.is_running:
                    break
                    
                try:
                    # 检查消息类型
                    if isinstance(message, bytes):
                        # 二进制消息，直接处理为图像数据
                        await self._handle_binary_message(message)
                    else:
                        # 文本消息，尝试解析JSON
                        data = json.loads(message)
                        await self._handle_json_message(data)
                except json.JSONDecodeError:
                    # 如果不是JSON，尝试作为二进制图像数据处理
                    await self._handle_binary_message(message)
                except Exception as e:
                    self.logger.error(f"处理消息错误: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.info("连接已关闭")
        except Exception as e:
            self.logger.error(f"监听消息错误: {e}")
    
    async def _handle_json_message(self, data):
        """处理JSON消息"""
        if 'image' in data:
            # 处理base64编码的图像
            await self._decode_base64_image(data['image'])
        elif 'status' in data:
            self.status_updated.emit(data['status'])
    
    async def _handle_binary_message(self, message):
        """处理二进制消息"""
        try:
            # 尝试将二进制数据解码为图像
            if isinstance(message, bytes):
                # 使用OpenCV解码图像
                nparr = np.frombuffer(message, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if image is not None:
                    self.current_image = image
                    self.image_count += 1
                    self.last_image_time = time.time()
                    self.image_received.emit(image)
        except Exception as e:
            self.logger.error(f"解码二进制图像错误: {e}")
    
    async def _decode_base64_image(self, base64_data):
        """解码base64图像数据"""
        try:
            import base64
            # 解码base64
            image_data = base64.b64decode(base64_data)
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is not None:
                self.current_image = image
                self.image_count += 1
                self.last_image_time = time.time()
                self.image_received.emit(image)
        except Exception as e:
            self.logger.error(f"解码base64图像错误: {e}")
    
    def get_connection_stats(self):
        """获取连接统计信息"""
        return {
            "connected": self.is_connected(),
            "image_count": self.image_count,
            "last_image_time": self.last_image_time,
            "current_url": self._get_current_url(),
            "reconnect_attempts": self.reconnect_attempts
        }
