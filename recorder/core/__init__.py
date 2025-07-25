"""
核心功能包
包含图像处理、录制会话等核心功能
"""

from .image_processor import ImageProcessor
from .recording_session import RecordingSession, MultiStageSession
from .multistage_manager import MultiStageManager

__all__ = [
    'ImageProcessor',
    'RecordingSession',
    'MultiStageSession',
    'MultiStageManager'
]
