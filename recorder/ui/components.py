"""
UI组件模块
包含ROI选择器、按钮等组件
"""

import time
from PyQt5.QtWidgets import QLabel, QPushButton
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRect, QPoint
from PyQt5.QtGui import QPixmap, QImage, QFont, QPalette, QColor, QPainter, QPen, QBrush


class ROISelector(QLabel):
    """
ROI选择器组件
用于在预览区域选择感兴趣区域
"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_point = None
        self.end_point = None
        self.roi_rect = None
        self.is_selecting = False
        self.setMinimumSize(400, 300)
        
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.start_point = event.pos()
            self.is_selecting = True
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.is_selecting and self.start_point:
            self.end_point = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.end_point = event.pos()
            self.is_selecting = False
            
            # 计算ROI矩形
            if self.start_point and self.end_point:
                x1, y1 = self.start_point.x(), self.start_point.y()
                x2, y2 = self.end_point.x(), self.end_point.y()
                
                x = min(x1, x2)
                y = min(y1, y2)
                w = abs(x2 - x1)
                h = abs(y2 - y1)
                
                if w > 10 and h > 10:  # 最小ROI尺寸
                    self.roi_rect = (x, y, w, h)
            
            self.update()
    
    def paintEvent(self, event):
        """绘制事件"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        
        # 绘制ROI选择框
        if self.is_selecting and self.start_point and self.end_point:
            pen = QPen(Qt.red, 2, Qt.DashLine)
            painter.setPen(pen)
            
            x1, y1 = self.start_point.x(), self.start_point.y()
            x2, y2 = self.end_point.x(), self.end_point.y()
            
            rect = QRect(min(x1, x2), min(y1, y2), abs(x2-x1), abs(y2-y1))
            painter.drawRect(rect)
        
        # 绘制已确认的ROI
        elif self.roi_rect:
            pen = QPen(Qt.green, 3, Qt.SolidLine)
            painter.setPen(pen)
            
            x, y, w, h = self.roi_rect
            rect = QRect(x, y, w, h)
            painter.drawRect(rect)
            
            # 添加ROI信息文字
            painter.setPen(QPen(Qt.green, 1))
            painter.drawText(x, y-5, f"ROI: {w}×{h}")
    
    def get_roi_rect(self):
        """获取ROI矩形"""
        return self.roi_rect
    
    def clear_roi(self):
        """清除ROI选择"""
        self.roi_rect = None
        self.start_point = None
        self.end_point = None
        self.update()


class ModernButton(QPushButton):
    """
现代化按钮组件
提供不同风格的按钮样式
"""
    
    def __init__(self, text="", button_type="primary", parent=None):
        super().__init__(text, parent)
        self.button_type = button_type
        self.setup_style()
        
    def setup_style(self):
        """设置按钮样式"""
        styles = {
            "primary": {
                "bg": "#28a745",
                "hover": "#218838",
                "text": "white"
            },
            "danger": {
                "bg": "#dc3545", 
                "hover": "#c82333",
                "text": "white"
            },
            "secondary": {
                "bg": "#6c757d",
                "hover": "#5a6268", 
                "text": "white"
            }
        }
        
        style = styles.get(self.button_type, styles["primary"])
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {style["bg"]};
                color: {style["text"]};
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 11pt;
                font-weight: 600;
                min-height: 20px;
                min-width: 140px;
            }}
            QPushButton:hover {{
                background-color: {style["hover"]};
            }}
            QPushButton:pressed {{
                background-color: {style["hover"]};
            }}
            QPushButton:disabled {{
                background-color: #e9ecef;
                color: #6c757d;
            }}
        """)
