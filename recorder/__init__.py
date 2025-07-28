"""
PaperTracker 图像录制工具
模块化的图像录制应用程序
"""

__version__ = "3.1.0"
__author__ = "PaperTracker Team"
__description__ = "洁录制界面"

# 导入主要组件
from .core.image_processor import ImageProcessor
from .core.recording_session import RecordingSession, MultiStageSession
from .core.multistage_manager import MultiStageManager
from .network.websocket_manager import WebSocketManager
from .ui.components import ROISelector, ModernButton
from .ui.dialogs import UserInfoDialog
from .ui.voice_guide import VoiceGuide
from .ui.enhanced_panels import RotationPanel, ROIPanel
from .ui.main_window import BaseRecorderWindow
from .ui.enhanced_recorder import EnhancedRecorderWindow
from .config.settings import AppSettings, RecordingStageConfig, AppConstants

__all__ = [
    'ImageProcessor',
    'RecordingSession', 
    'MultiStageSession',
    'MultiStageManager',
    'WebSocketManager',
    'ROISelector',
    'ModernButton', 
    'UserInfoDialog',
    'VoiceGuide',
    'RotationPanel',
    'ROIPanel',
    'BaseRecorderWindow',
    'EnhancedRecorderWindow',
    'AppSettings',
    'RecordingStageConfig',
    'AppConstants'
]
