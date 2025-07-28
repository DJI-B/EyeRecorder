#!/usr/bin/env python3
"""
PaperTracker 图像录制工具 - 完全重构版主入口文件
使用模块化的组件和更清晰的代码结构
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# 导入重构后的模块
from recorder.config import AppConstants
from recorder.ui import EnhancedRecorderWindow
from theme import apply_modern_theme


def setup_application():
    """
    设置应用程序
    配置基本属性和主题
    """
    # 在创建QApplication之前设置高DPI属性
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName(AppConstants.APP_NAME)
    app.setApplicationVersion(AppConstants.APP_VERSION)
    app.setApplicationDisplayName(AppConstants.APP_DISPLAY_NAME)
    
    # 应用现代主题
    apply_modern_theme(app)
    
    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    font.setHintingPreference(QFont.PreferDefaultHinting)
    app.setFont(font)
    
    return app


def create_main_window():
    """
    创建主窗口
    使用增强版录制器
    """
    window = EnhancedRecorderWindow()
    return window


def setup_window_animations(window):
    """
    设置窗口动画效果
    添加启动时的淡入效果
    """
    from PyQt5.QtCore import QPropertyAnimation, QEasingCurve
    
    window.setWindowOpacity(0.0)
    fade_in = QPropertyAnimation(window, b"windowOpacity")
    fade_in.setDuration(500)
    fade_in.setStartValue(0.0)
    fade_in.setEndValue(1.0)
    fade_in.setEasingCurve(QEasingCurve.OutCubic)
    fade_in.start()
    
    return fade_in


def main():
    """
    主函数
    应用程序的入口点
    """
    try:
        # 创建保存目录
        import os
        save_dir = os.path.join(os.path.dirname(__file__), 'saved_images')
        os.makedirs(save_dir, exist_ok=True)
        print(f"保存目录已创建: {save_dir}")
        
        # 初始化应用程序
        app = setup_application()
        
        # 创建主窗口
        window = create_main_window()
        window.show()
        
        # 设置动画效果
        fade_animation = setup_window_animations(window)
        
        # 运行应用程序
        sys.exit(app.exec_())
        
    except SystemExit:
        pass
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
