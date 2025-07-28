"""
增强版录制器实现 - 修复版
基于模块化组件的完整录制器实现，仅支持多阶段录制
"""

import time
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QGroupBox, QGridLayout, QMessageBox, QTabWidget,
    QLineEdit, QFileDialog, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage

from .main_window import BaseRecorderWindow
from .enhanced_panels import RotationPanel, ROIPanel
from .components import ModernButton
from ..core.image_processor import ImageProcessor


class EnhancedRecorderWindow(BaseRecorderWindow):
    """
    增强版录制器窗口
    仅支持多阶段录制，包含旋转、ROI等增强功能
    """
    
    def __init__(self):
        # 初始化增强功能参数
        self.rotation_angle = 0
        self.roi_enabled = False
        self.roi_coords = None
        self._roi_panel = None
        
        super().__init__()
        
        # 初始化增强功能组件
        self.setup_enhanced_components()
    
    def setup_enhanced_components(self):
        """初始化增强功能组件"""
        # 设置多阶段管理器的处理参数回调
        self.multistage_manager.set_processing_params_callback(self.get_processing_params)
        
        # 初始化ROI面板（现在preview_label已经可用）
        QTimer.singleShot(100, self.initialize_roi_panel_delayed)
    
    def initialize_roi_panel(self):
        """初始化ROI面板"""
        # ROI面板将在需要时延迟创建
        pass
    def initialize_roi_panel_delayed(self):
        """延迟初始化ROI面板"""
        if hasattr(self, 'preview_label') and hasattr(self, 'roi_layout'):
            self._roi_panel = ROIPanel(self.preview_label)
            self.roi_layout.addWidget(self._roi_panel)
    @property
    def roi_panel(self):
        """延迟创建ROI面板"""
        if not hasattr(self, '_roi_panel') or self._roi_panel is None:
            if hasattr(self, 'preview_label') and hasattr(self, 'roi_layout'):
                self._roi_panel = ROIPanel(self.preview_label)
                self.roi_layout.addWidget(self._roi_panel)
            else:
                return None
        return self._roi_panel
    
    @roi_panel.setter
    def roi_panel(self, value):
        """设置ROI面板"""
        self._roi_panel = value
    
    def create_control_panel(self) -> QWidget:
        """创建增强版控制面板"""
        panel = QWidget()
        panel.setMinimumWidth(420)
        panel.setStyleSheet("QWidget { background-color: transparent; }")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)
        
        # 应用标题
        title_group = self.create_title_section()
        layout.addWidget(title_group)
        
        # 创建选项卡
        tab_widget = self.create_tab_widget()
        layout.addWidget(tab_widget)
        
        layout.addStretch()
        return panel
    
    def create_title_section(self) -> QGroupBox:
        """创建标题区域"""
        group = QGroupBox()
        group.setStyleSheet("""
            QGroupBox {
                border: none;
                font-weight: bold;
                font-size: 12pt;
            }
        """)
        
        layout = QVBoxLayout()
        
        # 主标题
        title = QLabel("📷 PaperTracker 眼球数据录制工具")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 18pt;
                font-weight: bold;
                color: #2c3e50;
                padding: 20px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #74b9ff, stop:1 #0984e3);
                color: white;
                border-radius: 15px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title)
        
        # 副标题
        subtitle = QLabel("多阶段眼球录制 v3.1.0 - 专为研究设计")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            QLabel {
                font-size: 11pt;
                color: #636e72;
                font-style: italic;
                padding: 5px;
            }
        """)
        layout.addWidget(subtitle)
        
        group.setLayout(layout)
        return group
    
    def create_tab_widget(self) -> QTabWidget:
        """创建选项卡组件"""
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #dee2e6;
                border-radius: 8px;
                background-color: white;
                margin-top: -1px;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-bottom: none;
                border-radius: 6px 6px 0 0;
                padding: 8px 16px;
                margin-right: 2px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid white;
            }
            QTabBar::tab:hover {
                background-color: #e9ecef;
            }
        """)
        
        # 基础功能选项卡
        basic_tab = self.create_basic_tab()
        tab_widget.addTab(basic_tab, "🎯 录制控制")
        
        # 图像处理选项卡
        processing_tab = self.create_processing_tab()
        tab_widget.addTab(processing_tab, "🔧 图像处理")
        
        # 设置选项卡
        settings_tab = self.create_save_tab()
        tab_widget.addTab(settings_tab, "⚙️ 设置")
        
        return tab_widget
    
    def create_basic_tab(self) -> QWidget:
        """创建基础功能选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # 设备连接组
        connection_group = self.create_connection_group()
        layout.addWidget(connection_group)
        
        # 录制控制组 - 仅多阶段录制
        control_group = self.create_recording_control_group()
        layout.addWidget(control_group)
        
        # 录制状态组
        status_group = self.create_status_group()
        layout.addWidget(status_group)
        
        layout.addStretch()
        return tab
    
    def create_processing_tab(self) -> QWidget:
        """创建图像处理选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # 旋转设置组
        self.rotation_panel = RotationPanel()
        layout.addWidget(self.rotation_panel)
        
        # ROI设置组 - 延迟初始化
        self.roi_placeholder = QWidget()
        self.roi_layout = QVBoxLayout(self.roi_placeholder)
        layout.addWidget(self.roi_placeholder)
        
        layout.addStretch()
        return tab
    
    def create_save_tab(self) -> QWidget:
        """创建设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # 保存设置组
        save_group = self.create_save_group()
        layout.addWidget(save_group)
        
        layout.addStretch()
        return tab
    
    def create_connection_group(self) -> QGroupBox:
        """创建设备连接组"""
        group = QGroupBox("🔌 设备连接")
        layout = QVBoxLayout()
        
        # WebSocket URL输入
        url_layout = QHBoxLayout()
        url_label = QLabel("设备地址:")
        url_label.setStyleSheet("font-weight: 600;")
        url_layout.addWidget(url_label)
        
        self.websocket_url = QLineEdit()
        self.websocket_url.setText(self.app_settings.get_websocket_url())
        self.websocket_url.setPlaceholderText("输入WebSocket地址")
        self.websocket_url.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                font-size: 11pt;
            }
            QLineEdit:focus {
                border-color: #007bff;
            }
        """)
        url_layout.addWidget(self.websocket_url)
        layout.addLayout(url_layout)
        
        # 连接按钮
        button_layout = QHBoxLayout()
        
        self.connect_btn = ModernButton("🔗 连接设备", "primary")
        self.connect_btn.clicked.connect(self.connect_device)
        button_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = ModernButton("⛔ 断开连接", "danger")
        self.disconnect_btn.clicked.connect(self.disconnect_device)
        self.disconnect_btn.setEnabled(False)
        button_layout.addWidget(self.disconnect_btn)
        
        layout.addLayout(button_layout)
        
        group.setLayout(layout)
        return group
    
    def create_recording_control_group(self) -> QGroupBox:
        """创建录制控制组 - 仅多阶段录制"""
        group = QGroupBox("🎭 多阶段眼球录制")
        layout = QVBoxLayout()
        
        # 录制说明
        info_label = QLabel("📋 录制流程：正常眨眼 → 半睁眼 → 闭眼放松")
        info_label.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                padding: 10px;
                border-radius: 6px;
                color: #1565c0;
                font-weight: 600;
                border: 1px solid #bbdefb;
            }
        """)
        layout.addWidget(info_label)
        
        # 录制按钮
        button_layout = QHBoxLayout()
        
        self.start_recording_btn = ModernButton("🎬 开始眼球录制", "primary")
        self.start_recording_btn.clicked.connect(self.start_multi_stage_recording)
        button_layout.addWidget(self.start_recording_btn)
        
        # 停止录制按钮
        self.stop_record_btn = ModernButton("⏹️ 停止录制", "danger")
        self.stop_record_btn.clicked.connect(self.stop_recording)
        self.stop_record_btn.setEnabled(False)
        button_layout.addWidget(self.stop_record_btn)
        
        layout.addLayout(button_layout)
        
        group.setLayout(layout)
        return group
    
    def create_status_group(self) -> QGroupBox:
        """创建录制状态组"""
        group = QGroupBox("📊 录制状态")
        layout = QGridLayout()
        
        # 录制状态
        layout.addWidget(QLabel("录制状态:"), 0, 0)
        self.recording_status = QLabel("⚫ 等待开始")
        self.recording_status.setStyleSheet("font-weight: 600; color: #6c757d;")
        layout.addWidget(self.recording_status, 0, 1)
        
        # 图像数量
        layout.addWidget(QLabel("图像数量:"), 1, 0)
        self.image_count_label = QLabel("0 张")
        self.image_count_label.setStyleSheet("font-weight: 600; color: #28a745;")
        layout.addWidget(self.image_count_label, 1, 1)
        
        # 持续时间
        layout.addWidget(QLabel("持续时间:"), 2, 0)
        self.duration_label = QLabel("00:00:00")
        self.duration_label.setStyleSheet("font-weight: 600; color: #007bff;")
        layout.addWidget(self.duration_label, 2, 1)
        
        # 阶段信息
        layout.addWidget(QLabel("阶段信息:"), 3, 0)
        self.stage_info_label = QLabel("未开始")
        self.stage_info_label.setStyleSheet("font-weight: 600; color: #6c757d;")
        layout.addWidget(self.stage_info_label, 3, 1)
        
        group.setLayout(layout)
        return group
    
    def create_save_group(self) -> QGroupBox:
        """创建保存设置组"""
        group = QGroupBox("💾 保存设置")
        layout = QVBoxLayout()
        
        # 保存路径
        path_layout = QHBoxLayout()
        path_label = QLabel("保存路径:")
        path_label.setStyleSheet("font-weight: 600;")
        path_layout.addWidget(path_label)
        
        self.save_path = QLineEdit()
        self.save_path.setText(self.app_settings.get_save_path())
        self.save_path.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                font-size: 10pt;
            }
        """)
        path_layout.addWidget(self.save_path)
        
        browse_btn = QPushButton("📂 浏览")
        browse_btn.clicked.connect(self.browse_save_path)
        browse_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        path_layout.addWidget(browse_btn)
        
        layout.addLayout(path_layout)
        
        # 保存格式信息
        info_label = QLabel("📌 图像自动保存为 240×240 像素的高质量 JPG 格式")
        info_label.setStyleSheet("""
            QLabel {
                color: #28a745;
                font-weight: 600;
                padding: 8px;
                border: 1px solid #d4edda;
                border-radius: 4px;
                background-color: #d4edda;
            }
        """)
        layout.addWidget(info_label)
        
        group.setLayout(layout)
        return group
    
    def on_image_received(self, image):
        """接收到成功解码的图像时的处理"""
        # 调用父类方法更新current_image
        super().on_image_received(image)
        
        # 添加调试日志
        if hasattr(self, 'logger'):
            self.logger.debug(f"接收到图像，尺寸: {image.shape if image is not None else 'None'}")
    
    # 事件处理方法
    def connect_device(self):
        """连接设备"""
        url = self.websocket_url.text().strip()
        if not url:
            QMessageBox.warning(self, "⚠️ 警告", "请输入设备地址！")
            return
        
        self.app_settings.set_websocket_url(url)
        self.websocket_manager.set_url(url)
        self.websocket_manager.connect()
        
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
    
    def disconnect_device(self):
        """断开设备连接"""
        self.websocket_manager.disconnect()
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
    
    def browse_save_path(self):
        """浏览保存路径"""
        path = QFileDialog.getExistingDirectory(
            self, "选择保存目录", self.save_path.text()
        )
        if path:
            self.save_path.setText(path)
            self.app_settings.set_save_path(path)
    
    def start_multi_stage_recording(self):
        """开始多阶段录制"""
        success = self.multistage_manager.start_multi_stage_recording(
            self.user_info,
            self.save_path.text(),
            self.websocket_manager
        )
        
        if success:
            self.session_start_time = time.time()
            self.duration_timer.start(1000)
            self.start_recording_btn.setEnabled(False)
            self.stop_record_btn.setEnabled(True)
            self.recording_count = 0  # 重置计数
    
    def stop_recording(self):
        """停止录制"""
        try:
            # 停止定时器
            if hasattr(self, 'duration_timer') and self.duration_timer.isActive():
                self.duration_timer.stop()
            
            # 停止多阶段录制
            if hasattr(self, 'multistage_manager') and self.multistage_manager:
                self.multistage_manager.stop_multi_stage_recording()
            
            # 重置状态
            self.recording_status.setText("⏹️ 已停止")
            self.stage_info_label.setText("录制已停止")
            
            # 恢复按钮状态
            self.start_recording_btn.setEnabled(True)
            self.stop_record_btn.setEnabled(False)
            
            # 清理会话
            self.session_start_time = None
            
            self.logger.info("录制已停止")
            
        except Exception as e:
            self.logger.error(f"停止录制时出错: {e}")
            QMessageBox.warning(self, "⚠️ 错误", f"停止录制时出错: {e}")
    
    def get_processing_params(self):
        """获取处理参数"""
        # 确保面板存在
        if not hasattr(self, '_roi_panel') or self._roi_panel is None:
            roi_settings = {'enabled': False, 'coords': None}
        else:
            roi_settings = self._roi_panel.get_roi_settings()
        
        return {
            'rotation_angle': self.rotation_panel.get_rotation_angle(),
            'roi_enabled': roi_settings['enabled'],
            'roi_coords': roi_settings['coords'],
            'scale_factor': getattr(self, 'preview_scale_factor', 1.0)
        }
    
    def update_preview(self):
        """更新预览显示 - 应用旋转效果"""
        if self.current_image is not None:
            try:
                # 获取当前处理参数
                processing_params = self.get_processing_params()
                
                # 应用旋转到预览图像
                preview_image = self.current_image.copy()
                if processing_params['rotation_angle'] != 0:
                    preview_image = ImageProcessor.rotate_image(
                        preview_image, 
                        processing_params['rotation_angle']
                    )
                
                # 转换为Qt格式并显示
                height, width, channel = preview_image.shape
                bytes_per_line = 3 * width
                q_image = QImage(preview_image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
                
                # 缩放以适应预览区域
                preview_size = self.preview_label.size()
                scaled_pixmap = QPixmap.fromImage(q_image).scaled(
                    preview_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
                
                # 更新缩放因子
                self.preview_scale_factor = min(
                    preview_size.width() / width,
                    preview_size.height() / height
                )
                
                # 更新分辨率显示
                self.resolution_label.setText(f"📐 分辨率: {width}×{height}")
                
            except Exception as e:
                self.logger.error(f"更新预览失败: {e}")
    
    def update_duration(self):
        """更新持续时间显示"""
        if self.session_start_time:
            duration = int(time.time() - self.session_start_time)
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            seconds = duration % 60
            self.duration_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
    
    # 多阶段录制事件处理
    def on_stage_started(self, stage_number, stage_name):
        """阶段开始"""
        self.recording_status.setText(f"🎬 阶段 {stage_number}/3")
        self.stage_info_label.setText(f"阶段 {stage_number}: {stage_name}")
        self.logger.info(f"开始阶段 {stage_number}: {stage_name}")
    
    def on_stage_completed(self, stage_number, stage_name):
        """阶段完成"""
        self.stage_info_label.setText(f"✅ 阶段 {stage_number} 完成: {stage_name}")
        self.logger.info(f"完成阶段 {stage_number}: {stage_name}")
    
    def on_all_stages_completed(self):
        """所有阶段完成"""
        super().on_all_stages_completed()
        
        # 重置控件状态
        self.start_recording_btn.setEnabled(True)
        self.stop_record_btn.setEnabled(False)
        self.recording_status.setText("✅ 录制完成")
        self.stage_info_label.setText("🎉 所有阶段完成，数据包已创建")
        
        # 获取会话信息
        session_info = self.multistage_manager.get_session_info()
        if session_info:
            self.recording_count = session_info['count']
            self.image_count_label.setText(f"{self.recording_count} 张")
    
    def on_voice_message_changed(self, message):
        """语音消息变化"""
        self.stage_info_label.setText(message)
    
    def on_progress_updated(self, stage, current, progress_percent):
        """进度更新"""
        progress_text = f"阶段 {stage}: {current}张图像 ({progress_percent}%)"
        self.stage_info_label.setText(progress_text)
        
        # 更新图像计数
        session_info = self.multistage_manager.get_session_info()
        if session_info:
            self.recording_count = session_info['count']
            self.image_count_label.setText(f"{self.recording_count} 张")