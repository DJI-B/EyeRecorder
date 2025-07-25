"""
语音引导组件模块
提供多阶段录制的语音提示功能
"""

import time
import sys
from PyQt5.QtCore import QThread, pyqtSignal

# Cross-platform sound support
try:
    if sys.platform == "win32":
        import winsound
    else:
        # For macOS/Linux, we'll use a simple beep or skip sound
        import subprocess
except ImportError:
    winsound = None

def play_system_beep(beep_type="default"):
    """Cross-platform system beep function"""
    try:
        if sys.platform == "win32" and winsound:
            if beep_type == "info":
                winsound.MessageBeep(winsound.MB_ICONINFORMATION)
            elif beep_type == "asterisk":
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            elif beep_type == "ok":
                winsound.MessageBeep(winsound.MB_OK)
            else:
                winsound.MessageBeep(winsound.MB_OK)
        elif sys.platform == "darwin":  # macOS
            subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"], 
                         capture_output=True, check=False)
        else:  # Linux
            subprocess.run(["paplay", "/usr/share/sounds/alsa/Front_Left.wav"], 
                         capture_output=True, check=False)
    except Exception:
        # Fallback: print bell character
        print("\a", end="", flush=True)


class VoiceGuide(QThread):
    """
语音引导线程
用于在录制阶段提供语音提示和倒计时
"""
    finished = pyqtSignal()
    message_changed = pyqtSignal(str)
    countdown_changed = pyqtSignal(int)
    
    def __init__(self, messages, countdown_seconds=5):
        super().__init__()
        self.messages = messages  # 语音提示消息列表
        self.countdown_seconds = countdown_seconds
        self.should_stop = False
    
    def run(self):
        """运行语音提示"""
        try:
            # 播放语音提示
            for message in self.messages:
                if self.should_stop:
                    return
                    
                self.message_changed.emit(message)
                # 使用系统提示音
                play_system_beep("info")
                time.sleep(2)  # 每条消息间隔2秒
            
            # 倒计时
            for i in range(self.countdown_seconds, 0, -1):
                if self.should_stop:
                    return
                    
                self.countdown_changed.emit(i)
                self.message_changed.emit(f"准备开始录制... {i}")
                play_system_beep("asterisk")
                time.sleep(1)
            
            # 开始录制提示
            if not self.should_stop:
                self.message_changed.emit("开始录制！")
                play_system_beep("ok")
                self.finished.emit()
                
        except Exception as e:
            print(f"语音提示线程错误: {e}")
            self.finished.emit()
    
    def stop(self):
        """停止语音提示"""
        self.should_stop = True
