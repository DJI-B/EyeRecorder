"""
多阶段录制管理模块 - 修复版
管理多阶段录制的流程控制和状态管理
修复了图像保存问题
"""

import time
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QMessageBox

from ..config.settings import RecordingStageConfig
from .recording_session import MultiStageSession
from .image_processor import ImageProcessor


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
        self.websocket_client = None
        self.get_processing_params_callback = None
        
        # 添加阶段时间控制
        self.stage_start_time = None
        self.last_capture_time = 0
        
        # 添加日志记录器
        import logging
        self.logger = logging.getLogger(__name__)
        
        # 定时器
        self.stage_timer = QTimer()
        self.stage_timer.timeout.connect(self._capture_stage_image)
        
        # 阶段时长定时器
        self.stage_duration_timer = QTimer()
        self.stage_duration_timer.timeout.connect(self._complete_current_stage)
        
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
        
        # 保存WebSocket客户端引用
        self.websocket_client = websocket_client
        
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
        
        # 开始第一个阶段
        self._start_stage(0)
        
        return True
    
    def stop_multi_stage_recording(self):
        """停止多阶段录制"""
        self.is_multi_stage_active = False
        self.is_recording = False
        
        # 停止所有定时器
        self.stage_timer.stop()
        self.stage_duration_timer.stop()
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
        display_name = stage.get('display_name', stage['name'])
        self.stage_started.emit(stage_index + 1, display_name)
        
        # 启动语音引导 (lazy import to avoid circular import)
        from ..ui.voice_guide import VoiceGuide
        self.voice_guide = VoiceGuide(stage['voice_messages'], countdown_seconds=3)
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
        self.stage_start_time = time.time()
        self.last_capture_time = 0
        
        # 删除图像捕获定时器，现在收到图就立即录制
        # self.stage_timer.start(stage['interval_ms'])
        
        # 启动阶段时长定时器（5秒后自动完成）
        duration_ms = stage['duration_seconds'] * 1000
        self.stage_duration_timer.start(duration_ms)
        
        # 发送录制开始信号
        self.recording_started.emit(stage_index + 1)
        
        self.logger.info(f"开始阶段 {stage_index + 1} 录制: {stage.get('display_name', stage['name'])}, 时长: {stage['duration_seconds']}秒 - 收到图像立即录制")
    
    def capture_current_image(self):
        """捕获当前图像（由外部调用）"""
        return self._capture_stage_image()
    
    def _capture_stage_image(self):
        """阶段图像捕获（收到图像时触发）- 修复版"""
        if not self.is_multi_stage_active or not self.is_recording:
            return False
        
        if not self.websocket_client:
            self.logger.warning("WebSocket客户端不可用")
            return False
        
        # 添加最小间隔限制，防止过于频繁保存（可选，如果不需要可以删除）
        current_time = time.time()
        min_interval = 0.01  # 最小间隔50ms，避免过于频繁保存
        if current_time - self.last_capture_time < min_interval:
            return False
        self.last_capture_time = current_time
        
        # 获取当前图像
        current_image = self.websocket_client.get_current_image()
        if current_image is None:
            return False
        
        try:
            # 获取处理参数
            processing_params = self._get_processing_params()
            
            # 处理图像
            processed_image = self._process_image_for_saving(current_image, processing_params)
            if processed_image is None:
                self.logger.warning("图像处理失败")
                return False
            
            # 保存阶段图像
            filepath = self.session.save_stage_image(processed_image, processing_params)
            
            if filepath:
                self.stage_recording_count += 1
                
                # 更新进度（基于时间进度）
                stage = self.recording_stages[self.current_stage]
                elapsed_time = time.time() - self.stage_start_time
                progress_percent = min(100, int((elapsed_time / stage['duration_seconds']) * 100))
                
                # 发送进度更新信号
                self.progress_updated.emit(
                    self.current_stage + 1, 
                    self.stage_recording_count, 
                    progress_percent
                )
                
                return True
            else:
                self.logger.warning("图像保存失败")
                return False
                
        except Exception as e:
            self.logger.error(f"捕获阶段图像时出错: {e}")
            return False
    
    def _process_image_for_saving(self, image, processing_params):
        """处理图像用于保存 - 使用所见即所得方式"""
        try:
            if image is None:
                self.logger.warning("输入图像为空")
                return None
            
            # 使用所见即所得的处理方法
            if processing_params.get('preview_size'):
                # 有预览尺寸信息，使用所见即所得处理
                processed_image = ImageProcessor.process_image_pipeline_wysiwyg(
                    image,
                    rotation_angle=processing_params.get('rotation_angle', 0),
                    roi_coords=processing_params.get('roi_coords') if processing_params.get('roi_enabled') else None,
                    target_size=(240, 240),
                    preview_size=processing_params.get('preview_size')
                )
            else:
                # 没有预览尺寸信息，使用原来的方法
                processed_image = ImageProcessor.process_image_pipeline(
                    image,
                    rotation_angle=processing_params.get('rotation_angle', 0),
                    roi_coords=processing_params.get('roi_coords') if processing_params.get('roi_enabled') else None,
                    target_size=(240, 240),
                    scale_factor=processing_params.get('scale_factor', 1.0)
                )
            
            return processed_image
            
        except Exception as e:
            self.logger.error(f"处理图像失败: {e}")
            return None
    
    def _complete_current_stage(self):
        """完成当前阶段"""
        # 停止定时器
        self.stage_timer.stop()
        self.stage_duration_timer.stop()
        self.is_recording = False
        
        stage = self.recording_stages[self.current_stage]
        elapsed_time = time.time() - self.stage_start_time if self.stage_start_time else 0
        
        # 发送阶段完成信号
        self.stage_completed.emit(self.current_stage + 1, stage.get('display_name', stage['name']))
        self.recording_stopped.emit(self.current_stage + 1)
        
        self.logger.info(f"完成阶段 {self.current_stage + 1}: {stage.get('display_name', stage['name'])}, "
                        f"用时: {elapsed_time:.1f}秒, 采集: {self.stage_recording_count}张")
        
        # 切换到下一阶段
        self.session.next_stage()  # 调用session的next_stage方法
        
        # 短暂延迟后开始下一阶段（1.5秒过渡时间）
        QTimer.singleShot(1500, lambda: self._start_stage(self.current_stage + 1))
    
    def _complete_all_stages(self):
        """完成所有阶段"""
        import os
        self.is_multi_stage_active = False
        self.is_recording = False
        
        # 停止所有定时器
        self.stage_timer.stop()
        self.stage_duration_timer.stop()
        self.duration_timer.stop()
        
        # 创建汇总报告
        if self.session:
            self.session.create_multi_stage_summary()
            self.session.create_session_report()
            
            # 自动创建压缩包
            zip_path = self.session.create_session_package()
            if zip_path:
                self.logger.info(f"数据包已创建: {zip_path}")
                
                # 修复：改进的文件夹打开逻辑
                self._open_result_folder(zip_path)
                
                # 显示成功消息
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(
                    None,
                    "🎉 录制完成",
                    f"眼球数据录制已完成！\n\n"
                    f"数据包已自动创建：\n{os.path.basename(zip_path)}\n\n"
                    f"包含 {self.session.recording_count} 张图像\n\n"
                    f"保存位置：{os.path.dirname(zip_path)}"
                )
        
        # 发送完成信号
        self.all_stages_completed.emit()
    
    def _get_processing_params(self):
        """获取当前的图像处理参数"""
        if self.get_processing_params_callback:
            return self.get_processing_params_callback()
        else:
            # 返回默认参数
            return {
                'rotation_angle': 0,
                'roi_enabled': False,
                'roi_coords': None,
                'scale_factor': 1.0
            }
    
    def get_current_stage_info(self):
        """获取当前阶段信息"""
        if not self.is_multi_stage_active or self.current_stage >= len(self.recording_stages):
            return None
        
        stage = self.recording_stages[self.current_stage]
        
        # 计算时间进度
        elapsed_time = 0
        progress_percent = 0
        if self.stage_start_time and self.is_recording:
            elapsed_time = time.time() - self.stage_start_time
            progress_percent = min(100, int((elapsed_time / stage['duration_seconds']) * 100))
        
        return {
            'stage_number': self.current_stage + 1,
            'stage_name': stage['name'],
            'description': stage['description'],
            'current_count': self.stage_recording_count,
            'duration_seconds': stage['duration_seconds'],
            'elapsed_time': elapsed_time,
            'progress_percent': progress_percent,
            'progress': f"{elapsed_time:.1f}s/{stage['duration_seconds']}s ({progress_percent}%)",
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
        self.get_processing_params_callback = callback
    
    def _open_result_folder(self, zip_path):
        """打开结果文件夹 - 改进版"""
        import os
        import subprocess
        import sys
        
        try:
            folder_path = os.path.dirname(zip_path)
            
            # 确保路径存在
            if not os.path.exists(folder_path):
                self.logger.warning(f"文件夹不存在: {folder_path}")
                return
            
            if sys.platform.startswith('win'):
                # Windows: 使用explorer打开文件夹并选中压缩包
                subprocess.Popen(['explorer', '/select,', os.path.normpath(zip_path)])
            elif sys.platform.startswith('darwin'):
                # macOS: 使用Finder打开文件夹并选中文件
                subprocess.Popen(['open', '-R', zip_path])
            elif sys.platform.startswith('linux'):
                # Linux: 尝试多种文件管理器
                file_managers = ['nautilus', 'dolphin', 'thunar', 'pcmanfm', 'xdg-open']
                for fm in file_managers:
                    try:
                        if subprocess.call(['which', fm], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                            if fm == 'xdg-open':
                                subprocess.Popen([fm, folder_path])
                            else:
                                subprocess.Popen([fm, folder_path])
                            break
                    except:
                        continue
            else:
                self.logger.warning(f"不支持的操作系统: {sys.platform}")
                
            self.logger.info(f"已尝试打开文件夹: {folder_path}")
            
        except Exception as e:
            self.logger.warning(f"打开文件夹失败: {e}")