"""
配置设置模块
管理应用程序的各种配置和设置
"""

import os
from PyQt5.QtCore import QSettings


class AppSettings:
    """
    应用设置管理器
    负责管理用户配置和应用设置
    """
    
    def __init__(self):
        self.settings = QSettings('PaperTracker', 'ImageRecorder')
        self._init_default_settings()
    
    def _init_default_settings(self):
        """初始化默认设置"""
        defaults = {
            'websocket_url': 'ws://localhost:8080',
            'save_path': os.path.expanduser('~/Pictures/PaperTracker'),
            'auto_save_enabled': True,
            'auto_save_interval': 1000,  # 毫秒
            'image_quality': 95,
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
        default_path = os.path.expanduser('~/Pictures/PaperTracker')
        path = self.get('save_path', default_path)
        
        # 确保目录存在
        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
            except:
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
            'image_quality': self.get('image_quality', 95)
        }
    
    def set_image_processing_settings(self, rotation_angle=0, roi_enabled=False, quality=95):
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
    录制阶段配置
    定义多阶段录制的各个阶段配置
    """
    
    @staticmethod
    def get_default_stages():
        """获取默认录制阶段配置"""
        return [
            {
                "name": "正常眨眼",
                "description": "眼睛正常睁开，四处看，并且正常眨眼",
                "interval_ms": 300,
                "target_count": 100,
                "voice_messages": [
                    "请保持眼睛正常睁开",
                    "你可以四处看看，正常眨眼",
                    "请保持自然状态"
                ]
            },
            {
                "name": "闭眼状态",
                "description": "闭上眼睛，保持闭眼状态",
                "interval_ms": 400,
                "target_count": 80,
                "voice_messages": [
                    "请闭上眼睛",
                    "保持闭眼状态",
                    "放松眼部肌肉"
                ]
            },
            {
                "name": "眨眼动作",
                "description": "做大幅度的眨眼动作",
                "interval_ms": 250,
                "target_count": 120,
                "voice_messages": [
                    "请做大幅度的眨眼动作",
                    "用力眨眼，再睡开",
                    "重复眨眼动作"
                ]
            },
            {
                "name": "眼球转动",
                "description": "眼球左右上下转动，不要转头",
                "interval_ms": 350,
                "target_count": 90,
                "voice_messages": [
                    "请眼球左右上下转动",
                    "不要转动头部，只转动眼球",
                    "缓慢转动眼球"
                ]
            },
            {
                "name": "睁着状态",
                "description": "缓慢睁着，类似想睡觉的状态",
                "interval_ms": 500,
                "target_count": 60,
                "voice_messages": [
                    "请保持缓慢睁着的状态",
                    "类似想睡觉时的状态",
                    "眼睑可以略微下垂"
                ]
            }
        ]
    
    @staticmethod
    def validate_stage_config(stage_config):
        """验证阶段配置的有效性"""
        required_fields = ['name', 'description', 'interval_ms', 'target_count', 'voice_messages']
        
        for field in required_fields:
            if field not in stage_config:
                return False, f"缺少必要字段: {field}"
        
        if not isinstance(stage_config['interval_ms'], int) or stage_config['interval_ms'] <= 0:
            return False, "interval_ms 必须是正整数"
        
        if not isinstance(stage_config['target_count'], int) or stage_config['target_count'] <= 0:
            return False, "target_count 必须是正整数"
        
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
    DEFAULT_SAVE_PATH = "~/Pictures/PaperTracker"
    
    # 图像设置
    TARGET_IMAGE_SIZE = (240, 240)
    DEFAULT_IMAGE_QUALITY = 95
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
