"""
主窗口模块
包含主窗口的基础结构和布局
"""

import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSplitter, QStatusBar, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QSettings
from PyQt5.QtGui import QPixmap, QImage

from ..config.settings import AppSettings, AppConstants
from ..network.websocket_manager import WebSocketManager
from ..core.image_processor import ImageProcessor
from ..core.recording_session import RecordingSession
from ..core.multistage_manager import MultiStageManager
from .components import ROISelector
from .dialogs import UserInfoDialog


class BaseRecorderWindow(QMainWindow):
    """
    录制器基础主窗口
    提供基本的窗口结构和通用功能
    """
    
    def __init__(self):
        super().__init__()
        self.setup_logging()
        self.init_variables()
        self.check_user_info()
        self.setup_ui()
        self.setup_connections()
        self.load_settings()
        
        self.logger.info("PaperTracker 图像录制工具启动完成")
    
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def init_variables(self):
        """初始化变量"""
        # 应用设置
        self.app_settings = AppSettings()
        
        # 网络管理
        self.websocket_manager = WebSocketManager()
        
        # 录制管理
        self.recording_session = None
        self.multistage_manager = MultiStageManager()
        
        # UI相关
        self.current_image = None
        self.preview_scale_factor = 1.0
        
        # 用户信息
        self.user_info = {'username': '', 'email': ''}
        
        # 定时器
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview)
        
        self.duration_timer = QTimer()
        self.duration_timer.timeout.connect(self.update_duration)
        
        # 计数器
        self.recording_count = 0
        self.session_start_time = None
    
    def check_user_info(self):
        """检查用户信息"""
        saved_user_info = self.app_settings.get_user_info()
        if not saved_user_info.get('username') or not saved_user_info.get('email'):
            dialog = UserInfoDialog(self)
            if dialog.exec_() == dialog.Accepted:
                self.user_info = dialog.get_user_info()
                self.app_settings.set_user_info(self.user_info)
            else:
                # 用户取消，使用默认值
                self.user_info = {'username': 'User', 'email': 'user@example.com'}
        else:
            self.user_info = saved_user_info
    
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle(AppConstants.APP_DISPLAY_NAME)
        self.resize(1400, 900)
        
        # 主窗口中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # 创建分隔器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 控制面板
        control_panel = self.create_control_panel()
        splitter.addWidget(control_panel)
        
        # 预览面板
        preview_panel = self.create_preview_panel()
        splitter.addWidget(preview_panel)
        
        # 设置分隔器比例
        splitter.setStretchFactor(0, 0)  # 控制面板固定宽度
        splitter.setStretchFactor(1, 1)  # 预览面板可伸缩
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("🚀 应用程序已启动")
    
    def create_control_panel(self) -> QWidget:
        """创建控制面板（子类实现）"""
        panel = QWidget()
        panel.setMinimumWidth(AppConstants.CONTROL_PANEL_MIN_WIDTH)
        return panel
    
    def create_preview_panel(self) -> QWidget:
        """创建预览面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # 预览标题
        title = QLabel("📺 实时预览")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 16pt;
                font-weight: bold;
                color: #495057;
                padding: 15px;
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 10px;
                border: 2px solid #dee2e6;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title)
        
        # 预览区域使用ROI选择器
        self.preview_label = ROISelector()
        self.preview_label.setMinimumSize(*AppConstants.PREVIEW_MIN_SIZE)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #000000;
                border: 3px solid #007bff;
                border-radius: 12px;
                color: white;
                font-size: 14pt;
                font-weight: 600;
            }
        """)
        self.preview_label.setText("📱 等待设备连接...")
        layout.addWidget(self.preview_label)
        
        # 预览信息面板
        info_panel = self.create_preview_info_panel()
        layout.addWidget(info_panel)
        
        return panel
    
    def create_preview_info_panel(self) -> QWidget:
        """创建预览信息面板"""
        info_panel = QWidget()
        info_layout = QHBoxLayout(info_panel)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        # 分辨率信息
        self.resolution_label = QLabel("📐 分辨率: 等待连接")
        self.resolution_label.setStyleSheet(self._get_info_label_style())
        info_layout.addWidget(self.resolution_label)
        
        # FPS信息
        self.fps_label = QLabel("⚡ FPS: 0")
        self.fps_label.setStyleSheet(self._get_info_label_style())
        info_layout.addWidget(self.fps_label)
        
        # 图像质量
        self.quality_label = QLabel("🎨 质量: 高质量")
        self.quality_label.setStyleSheet("""
            QLabel {
                background-color: #d4edda;
                padding: 8px 12px;
                border-radius: 6px;
                color: #155724;
                font-size: 10pt;
                border: 1px solid #c3e6cb;
            }
        """)
        info_layout.addWidget(self.quality_label)
        
        info_layout.addStretch()
        return info_panel
    
    def setup_connections(self):
        """设置信号连接"""
        # WebSocket连接信号
        self.websocket_manager.connected.connect(self.on_websocket_connected)
        self.websocket_manager.disconnected.connect(self.on_websocket_disconnected)
        self.websocket_manager.error_occurred.connect(self.on_websocket_error)
        self.websocket_manager.image_received.connect(self.on_image_received)
        self.websocket_manager.status_updated.connect(self.on_status_updated)
        
        # 多阶段录制信号
        self.multistage_manager.stage_started.connect(self.on_stage_started)
        self.multistage_manager.stage_completed.connect(self.on_stage_completed)
        self.multistage_manager.all_stages_completed.connect(self.on_all_stages_completed)
        self.multistage_manager.voice_message_changed.connect(self.on_voice_message_changed)
        self.multistage_manager.progress_updated.connect(self.on_progress_updated)
    
    def load_settings(self):
        """加载设置"""
        # 加载窗口设置
        window_settings = self.app_settings.get_window_settings()
        if window_settings['geometry']:
            self.restoreGeometry(window_settings['geometry'])
        if window_settings['state']:
            self.restoreState(window_settings['state'])
    
    def save_settings(self):
        """保存设置"""
        self.app_settings.set_window_settings(
            self.saveGeometry(),
            self.saveState()
        )
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.save_settings()
        self.websocket_manager.disconnect()
        self.multistage_manager.stop_multi_stage_recording()
        event.accept()
    
    # 事件处理方法（子类可以重写）
    def on_websocket_connected(self):
        """
WebSocket连接成功"""
        self.preview_timer.start(33)  # ~30 FPS
        self.status_bar.showMessage("✅ 设备已连接")
    
    def on_websocket_disconnected(self):
        """
WebSocket连接断开"""
        self.preview_timer.stop()
        self.current_image = None
        self.preview_label.setText("📱 等待设备连接...")
        self.status_bar.showMessage("⚠️ 设备已断开")
    
    def on_websocket_error(self, error_msg):
        """
WebSocket错误"""
        self.status_bar.showMessage(f"❌ 连接错误: {error_msg}")
    
    def on_image_received(self, image):
        """接收到图像"""
        self.current_image = image
        
        # 收到图就立即录制 - 如果正在进行多阶段录制，自动保存图像
        if self.multistage_manager.is_active():
            self.multistage_manager.capture_current_image()
    
    def on_status_updated(self, status):
        """状态更新"""
        self.status_bar.showMessage(status)
    
    def update_preview(self):
        """更新预览显示（子类实现）"""
        pass
    
    def update_duration(self):
        """更新持续时间显示（子类实现）"""
        pass
    
    # 多阶段录制事件处理
    def on_stage_started(self, stage_number, stage_name):
        """阶段开始"""
        pass
    
    def on_stage_completed(self, stage_number, stage_name):
        """阶段完成"""
        pass
    
    def on_all_stages_completed(self):
        """所有阶段完成"""
        QMessageBox.information(
            self,
            "🎉 录制完成",
            f"多阶段录制已完成！\n\n总计保存: {self.recording_count} 张图像"
        )
    
    def on_voice_message_changed(self, message):
        """语音消息变化"""
        pass
    
    def on_progress_updated(self, stage, current, total):
        """进度更新"""
        pass
    
    def _get_info_label_style(self):
        """获取信息标签样式"""
        return """
            QLabel {
                background-color: #f8f9fa;
                padding: 8px 12px;
                border-radius: 6px;
                color: #495057;
                font-size: 10pt;
                border: 1px solid #dee2e6;
            }
        """
