"""
配置设置模块 - 修复版
管理应用程序的各种配置和设置
修复了保存路径问题
"""

import os
from PyQt5.QtCore import QSettings


class AppSettings:
    """
    应用设置管理器 - 修复版
    负责管理用户配置和应用设置
    """
    
    def __init__(self):
        self.settings = QSettings('PaperTracker', 'ImageRecorder')
        self._init_default_settings()
    
    def _init_default_settings(self):
        """初始化默认设置"""
        # 获取当前脚本的目录作为程序根目录
        import sys
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe
            program_root = os.path.dirname(sys.executable)
        else:
            # 如果是脚本运行
            program_root = os.path.dirname(os.path.abspath(__file__))
            # 向上找到项目根目录（包含main.py的目录）
            while program_root and not os.path.exists(os.path.join(program_root, 'main.py')):
                parent = os.path.dirname(program_root)
                if parent == program_root:  # 到达根目录
                    break
                program_root = parent
        
        default_save_path = os.path.join(program_root, 'saved_images')
        
        defaults = {
            'websocket_url': 'ws://localhost:8080',
            'save_path': default_save_path,
            'auto_save_enabled': True,
            'auto_save_interval': 1000,  # 毫秒
            'image_quality': 100,
            'rotation_angle': 0,
            'roi_enabled': False,
            'window_geometry': None,
            'window_state': None,
            'theme': 'modern',
            'last_user': {'username': '', 'email': ''}
        }
        
        for key, value in defaults.items():
            if not self.settings.contains(key):
                self.settings.setValue(key, value)
    
    def get(self, key, default_value=None):
        """获取设置值"""
        return self.settings.value(key, default_value)
    
    def set(self, key, value):
        """设置值"""
        self.settings.setValue(key, value)
        self.settings.sync()
    
    def get_websocket_url(self):
        """获取WebSocket URL"""
        return self.get('websocket_url', 'ws://localhost:8080')
    
    def set_websocket_url(self, url):
        """设置WebSocket URL"""
        self.set('websocket_url', url)
    
    def get_save_path(self):
        """获取保存路径"""
        # 获取当前脚本的目录作为程序根目录
        import sys
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe
            program_root = os.path.dirname(sys.executable)
        else:
            # 如果是脚本运行
            program_root = os.path.dirname(os.path.abspath(__file__))
            # 向上找到项目根目录（包含main.py的目录）
            while program_root and not os.path.exists(os.path.join(program_root, 'main.py')):
                parent = os.path.dirname(program_root)
                if parent == program_root:  # 到达根目录
                    break
                program_root = parent
        
        default_path = os.path.join(program_root, 'saved_images')
        path = self.get('save_path', default_path)
        
        # 确保目录存在
        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
            except Exception as e:
                print(f"创建保存目录失败: {e}")
                path = default_path
                os.makedirs(path, exist_ok=True)
        
        return path
    
    def set_save_path(self, path):
        """设置保存路径"""
        self.set('save_path', path)
    
    def get_auto_save_settings(self):
        """获取自动保存设置"""
        return {
            'enabled': self.get('auto_save_enabled', True),
            'interval': self.get('auto_save_interval', 1000)
        }
    
    def set_auto_save_settings(self, enabled, interval):
        """设置自动保存设置"""
        self.set('auto_save_enabled', enabled)
        self.set('auto_save_interval', interval)
    
    def get_image_processing_settings(self):
        """获取图像处理设置"""
        return {
            'rotation_angle': self.get('rotation_angle', 0),
            'roi_enabled': self.get('roi_enabled', False),
            'image_quality': self.get('image_quality', 100)
        }
    
    def set_image_processing_settings(self, rotation_angle=0, roi_enabled=False, quality=100):
        """设置图像处理设置"""
        self.set('rotation_angle', rotation_angle)
        self.set('roi_enabled', roi_enabled)
        self.set('image_quality', quality)
    
    def get_window_settings(self):
        """获取窗口设置"""
        return {
            'geometry': self.get('window_geometry'),
            'state': self.get('window_state')
        }
    
    def set_window_settings(self, geometry, state):
        """设置窗口设置"""
        self.set('window_geometry', geometry)
        self.set('window_state', state)
    
    def get_user_info(self):
        """获取用户信息"""
        return self.get('last_user', {'username': '', 'email': ''})
    
    def set_user_info(self, user_info):
        """设置用户信息"""
        self.set('last_user', user_info)
    
    def reset_to_defaults(self):
        """重置为默认设置"""
        self.settings.clear()
        self._init_default_settings()


class RecordingStageConfig:
    """
    录制阶段配置 - 修复版
    定义多阶段录制的各个阶段配置
    """
    
    @staticmethod
    def get_default_stages():
        """获取眼球数据录制的阶段配置"""
        return [
            {
                "name": "normal_blink",  # 使用英文名避免路径问题
                "display_name": "正常眨眼",  # 显示用的中文名
                "description": "眼睛正常睁开，四处看，自然眨眼",
                "duration_seconds": 5,  # 录制时长5秒
                "interval_ms": 200,     # 采集间隔200ms，提高频率
                "voice_messages": [
                    "请保持眼睛正常睁开",
                    "您可以四处看看，正常眨眼",
                    "保持自然放松的状态"
                ]
            },
            {
                "name": "half_open",
                "display_name": "半睁眼",
                "description": "眼睛半睁开，四处看，不要眨眼",
                "duration_seconds": 5,  # 录制时长5秒
                "interval_ms": 200,     # 采集间隔200ms
                "voice_messages": [
                    "请将眼睛半睁开",
                    "保持半睁眼状态，不要眨眼",
                    "眼球可以四处看"
                ]
            },
            {
                "name": "closed_relax",
                "display_name": "闭眼放松",
                "description": "完全闭眼，保持放松状态",
                "duration_seconds": 5,  # 录制时长5秒
                "interval_ms": 200,     # 采集间隔200ms
                "voice_messages": [
                    "请完全闭上眼睛",
                    "保持放松状态",
                    "不要用力，自然闭眼即可"
                ]
            }
        ]
    
    @staticmethod
    def validate_stage_config(stage_config):
        """验证阶段配置的有效性"""
        required_fields = ['name', 'description', 'duration_seconds', 'interval_ms', 'voice_messages']
        
        for field in required_fields:
            if field not in stage_config:
                return False, f"缺少必要字段: {field}"
        
        if not isinstance(stage_config['duration_seconds'], int) or stage_config['duration_seconds'] <= 0:
            return False, "duration_seconds 必须是正整数"
        
        if not isinstance(stage_config['interval_ms'], int) or stage_config['interval_ms'] <= 0:
            return False, "interval_ms 必须是正整数"
        
        if not isinstance(stage_config['voice_messages'], list) or len(stage_config['voice_messages']) == 0:
            return False, "voice_messages 必须是非空列表"
        
        return True, "OK"


class AppConstants:
    """
    应用常量定义
    """
    
    # 应用信息
    APP_NAME = "PaperTracker图像录制工具"
    APP_VERSION = "3.1.0"
    APP_DISPLAY_NAME = "📷 PaperTracker 图像录制工具 (增强版)"
    
    # 文件路径
    DEFAULT_SAVE_PATH = "./saved_images"
    
    # 图像设置
    TARGET_IMAGE_SIZE = (240, 240)
    DEFAULT_IMAGE_QUALITY = 100
    SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp']
    
    # 网络设置
    DEFAULT_WEBSOCKET_URL = "ws://localhost:8080"
    CONNECTION_TIMEOUT = 10  # 秒
    MAX_RECONNECT_ATTEMPTS = 5
    RECONNECT_DELAY = 3  # 秒
    
    # UI设置
    PREVIEW_MIN_SIZE = (640, 480)
    CONTROL_PANEL_MIN_WIDTH = 420
    
    # 录制设置
    DEFAULT_AUTO_SAVE_INTERVAL = 1000  # 毫秒
    MIN_ROI_SIZE = 10  # 像素