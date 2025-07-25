"""
多阶段录制管理模块
管理多阶段录制的流程控制和状态管理
"""

import time
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QMessageBox

from ..config.settings import RecordingStageConfig
from .recording_session import MultiStageSession


class MultiStageManager(QObject):
    """
    多阶段录制管理器
    管理多阶段录制的整个流程
    """
    
    # 信号定义
    stage_started = pyqtSignal(int, str)  # 阶段开始
    stage_completed = pyqtSignal(int, str)  # 阶段完成
    recording_started = pyqtSignal(int)  # 录制开始
    recording_stopped = pyqtSignal(int)  # 录制停止
    all_stages_completed = pyqtSignal()  # 所有阶段完成
    voice_message_changed = pyqtSignal(str)  # 语音消息变化
    countdown_changed = pyqtSignal(int)  # 倒计时变化
    progress_updated = pyqtSignal(int, int, int)  # 进度更新 (stage, current, total)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.recording_stages = RecordingStageConfig.get_default_stages()
        self.current_stage = 0
        self.stage_recording_count = 0
        self.is_recording = False
        self.is_multi_stage_active = False
        self.session = None
        self.voice_guide = None
        
        # 定时器
        self.stage_timer = QTimer()
        self.stage_timer.timeout.connect(self._capture_stage_image)
        
        self.duration_timer = QTimer()
        self.session_start_time = None
    
    def set_recording_stages(self, stages):
        """设置录制阶段配置"""
        self.recording_stages = stages
    
    def start_multi_stage_recording(self, user_info, save_path, websocket_client):
        """开始多阶段录制"""
        if not websocket_client or not websocket_client.is_connected():
            QMessageBox.warning(None, "⚠️ 警告", "请先连接设备！")
            return False
        
        # 初始化会话
        self.session = MultiStageSession(user_info, save_path, self.recording_stages)
        if not self.session.current_session_folder:
            QMessageBox.critical(None, "❌ 错误", "无法创建保存文件夹")
            return False
        
        # 初始化状态
        self.is_multi_stage_active = True
        self.current_stage = 0
        self.stage_recording_count = 0
        self.session_start_time = time.time()
        self.websocket_client = websocket_client
        
        # 开始第一个阶段
        self._start_stage(0)
        
        return True
    
    def stop_multi_stage_recording(self):
        """停止多阶段录制"""
        self.is_multi_stage_active = False
        self.is_recording = False
        # self.stage_timer.stop()  # 已注释掉定时器
        self.duration_timer.stop()
        
        if self.voice_guide:
            self.voice_guide.stop()
            self.voice_guide = None
    
    def _start_stage(self, stage_index):
        """开始指定阶段"""
        if stage_index >= len(self.recording_stages):
            self._complete_all_stages()
            return
        
        stage = self.recording_stages[stage_index]
        self.current_stage = stage_index
        self.stage_recording_count = 0
        
        # 发送阶段开始信号
        self.stage_started.emit(stage_index + 1, stage['name'])
        
        # 启动语音引导 (lazy import to avoid circular import)
        from ..ui.voice_guide import VoiceGuide
        self.voice_guide = VoiceGuide(stage['voice_messages'], countdown_seconds=5)
        self.voice_guide.message_changed.connect(self.voice_message_changed.emit)
        self.voice_guide.countdown_changed.connect(self.countdown_changed.emit)
        self.voice_guide.finished.connect(lambda: self._start_stage_recording(stage_index))
        self.voice_guide.start()
    
    def _start_stage_recording(self, stage_index):
        """开始阶段录制"""
        if stage_index != self.current_stage:
            return  # 防止延迟的信号
        
        stage = self.recording_stages[stage_index]
        self.is_recording = True
        self.stage_recording_count = 0
        
        # 注释掉定时器，改为通过image_received事件触发保存
        # self.stage_timer.start(stage['interval_ms'])
        
        # 发送录制开始信号
        self.recording_started.emit(stage_index + 1)
    
    def capture_current_image(self):
        """捕获当前图像（由外部调用）"""
        return self._capture_stage_image()
    
    def _capture_stage_image(self):
        """阶段图像捕获"""
        if not self.is_multi_stage_active or not self.is_recording:
            return
        
        if not self.websocket_client:
            return
        
        # 获取当前图像
        current_image = self.websocket_client.get_current_image()
        if current_image is None:
            return
        
        # 保存阶段图像
        processing_params = self._get_processing_params()
        filepath = self.session.save_stage_image(current_image, processing_params)
        
        if filepath:
            self.stage_recording_count += 1
            
            # 更新进度
            stage = self.recording_stages[self.current_stage]
            self.progress_updated.emit(self.current_stage + 1, 
                                     self.stage_recording_count, 
                                     stage['target_count'])
            
            # 检查是否完成当前阶段
            if self.stage_recording_count >= stage['target_count']:
                self._complete_current_stage()
    
    def _complete_current_stage(self):
        """完成当前阶段"""
        # self.stage_timer.stop()  # 已注释掉定时器
        self.is_recording = False
        
        stage = self.recording_stages[self.current_stage]
        
        # 发送阶段完成信号
        self.stage_completed.emit(self.current_stage + 1, stage['name'])
        self.recording_stopped.emit(self.current_stage + 1)
        
        # 短暂延迟后开始下一阶段
        QTimer.singleShot(2000, lambda: self._start_stage(self.current_stage + 1))
    
    def _complete_all_stages(self):
        """完成所有阶段"""
        self.is_multi_stage_active = False
        self.is_recording = False
        # self.stage_timer.stop()  # 已注释掉定时器
        self.duration_timer.stop()
        
        # 创建汇总报告
        if self.session:
            self.session.create_multi_stage_summary()
            self.session.create_session_report()
        
        # 发送完成信号
        self.all_stages_completed.emit()
    
    def _get_processing_params(self):
        """获取当前的图像处理参数"""
        # 这里需要从主窗口获取处理参数
        # 暂时返回空字典，实际使用时需要传入参数
        return {}
    
    def get_current_stage_info(self):
        """获取当前阶段信息"""
        if not self.is_multi_stage_active or self.current_stage >= len(self.recording_stages):
            return None
        
        stage = self.recording_stages[self.current_stage]
        return {
            'stage_number': self.current_stage + 1,
            'stage_name': stage['name'],
            'description': stage['description'],
            'current_count': self.stage_recording_count,
            'target_count': stage['target_count'],
            'progress': f"{self.stage_recording_count}/{stage['target_count']}",
            'is_recording': self.is_recording
        }
    
    def get_session_info(self):
        """获取会话信息"""
        if not self.session:
            return None
        return self.session.get_session_info()
    
    def is_active(self):
        """检查是否正在进行多阶段录制"""
        return self.is_multi_stage_active
    
    def set_processing_params_callback(self, callback):
        """设置获取处理参数的回调函数"""
        self._get_processing_params = callback
