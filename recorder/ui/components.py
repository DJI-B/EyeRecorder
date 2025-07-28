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
    ROI选择器组件 - 智能版本
    用于在预览区域选择感兴趣区域，自动处理黑条偏移问题
    """
    
    # 添加ROI选择完成的信号
    roi_selected = pyqtSignal(tuple)  # 发送ROI坐标 (x, y, w, h)
    roi_cleared = pyqtSignal()        # 发送ROI清除信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_point = None
        self.end_point = None
        self.roi_rect = None
        self.is_selecting = False
        self.setMinimumSize(400, 300)
        
        # 添加：记录实际图像在预览中的位置和尺寸
        self.image_rect = None  # 实际图像在预览中的矩形区域
        self.original_image_size = None  # 原始图像尺寸 (width, height)
        self.scale_factor = 1.0  # 缩放因子
    
    def setPixmap(self, pixmap):
        """重写setPixmap，计算图像在预览中的实际位置和缩放因子"""
        super().setPixmap(pixmap)
        
        if pixmap and not pixmap.isNull():
            # 计算图像在标签中的实际显示区域
            label_size = self.size()
            pixmap_size = pixmap.size()
            
            # 计算居中显示的位置
            x_offset = (label_size.width() - pixmap_size.width()) // 2
            y_offset = (label_size.height() - pixmap_size.height()) // 2
            
            # 记录图像实际显示区域
            self.image_rect = QRect(x_offset, y_offset, 
                                  pixmap_size.width(), pixmap_size.height())
            
            # 计算缩放因子（如果有原始图像尺寸信息）
            if self.original_image_size:
                original_width, original_height = self.original_image_size
                self.scale_factor = min(
                    pixmap_size.width() / original_width,
                    pixmap_size.height() / original_height
                )
    
    def mousePressEvent(self, event):
        """鼠标按下事件 - 检查是否在有效图像区域内"""
        if event.button() == Qt.LeftButton:
            click_pos = event.pos()
            
            # 检查点击位置是否在实际图像区域内
            if self.image_rect and self.image_rect.contains(click_pos):
                # 转换为相对于图像的坐标
                relative_x = click_pos.x() - self.image_rect.x()
                relative_y = click_pos.y() - self.image_rect.y()
                self.start_point = QPoint(relative_x, relative_y)
                self.is_selecting = True
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 限制在有效图像区域内"""
        if self.is_selecting and self.start_point and self.image_rect:
            mouse_pos = event.pos()
            
            # 将鼠标位置限制在图像区域内
            constrained_x = max(self.image_rect.x(), 
                              min(mouse_pos.x(), self.image_rect.right()))
            constrained_y = max(self.image_rect.y(), 
                              min(mouse_pos.y(), self.image_rect.bottom()))
            
            # 转换为相对于图像的坐标
            relative_x = constrained_x - self.image_rect.x()
            relative_y = constrained_y - self.image_rect.y()
            
            self.end_point = QPoint(relative_x, relative_y)
            self.update()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 计算最终ROI（转换为原始图像坐标）"""
        if event.button() == Qt.LeftButton and self.is_selecting:
            mouse_pos = event.pos()
            
            if self.image_rect and self.image_rect.contains(mouse_pos):
                # 转换为相对于图像的坐标
                relative_x = mouse_pos.x() - self.image_rect.x()
                relative_y = mouse_pos.y() - self.image_rect.y()
                self.end_point = QPoint(relative_x, relative_y)
            
            self.is_selecting = False
            
            # 计算ROI矩形（基于预览图像坐标系）
            if self.start_point and self.end_point:
                x1, y1 = self.start_point.x(), self.start_point.y()
                x2, y2 = self.end_point.x(), self.end_point.y()
                
                preview_x = min(x1, x2)
                preview_y = min(y1, y2)
                preview_w = abs(x2 - x1)
                preview_h = abs(y2 - y1)
                
                if preview_w > 10 and preview_h > 10:  # 最小ROI尺寸
                    # 转换为原始图像坐标
                    if self.scale_factor > 0:
                        original_x = int(preview_x / self.scale_factor)
                        original_y = int(preview_y / self.scale_factor)
                        original_w = int(preview_w / self.scale_factor)
                        original_h = int(preview_h / self.scale_factor)
                        
                        # 存储原始图像坐标
                        self.roi_rect = (original_x, original_y, original_w, original_h)
                        
                        # 发送原始图像坐标
                        self.roi_selected.emit(self.roi_rect)
                    else:
                        print("[WARNING] 缩放因子无效，无法转换ROI坐标")
            
            self.update()
    
    def paintEvent(self, event):
        """绘制事件 - 绘制ROI选择框"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        
        # 只在有效图像区域内绘制
        if not self.image_rect:
            return
        
        # 绘制ROI选择框（转换回预览坐标）
        if self.is_selecting and self.start_point and self.end_point:
            pen = QPen(Qt.red, 2, Qt.DashLine)
            painter.setPen(pen)
            
            # 转换为预览坐标
            x1 = self.start_point.x() + self.image_rect.x()
            y1 = self.start_point.y() + self.image_rect.y()
            x2 = self.end_point.x() + self.image_rect.x()
            y2 = self.end_point.y() + self.image_rect.y()
            
            rect = QRect(min(x1, x2), min(y1, y2), abs(x2-x1), abs(y2-y1))
            painter.drawRect(rect)
        
        # 绘制已确认的ROI（从原始坐标转换为预览坐标）
        elif self.roi_rect and self.scale_factor > 0:
            pen = QPen(Qt.green, 3, Qt.SolidLine)
            painter.setPen(pen)
            
            # 原始图像坐标
            orig_x, orig_y, orig_w, orig_h = self.roi_rect
            
            # 转换为预览坐标
            preview_x = int(orig_x * self.scale_factor) + self.image_rect.x()
            preview_y = int(orig_y * self.scale_factor) + self.image_rect.y()
            preview_w = int(orig_w * self.scale_factor)
            preview_h = int(orig_h * self.scale_factor)
            
            rect = QRect(preview_x, preview_y, preview_w, preview_h)
            painter.drawRect(rect)
            
            # 添加ROI信息文字（显示原始图像尺寸）
            painter.setPen(QPen(Qt.green, 1))
            painter.drawText(preview_x, preview_y-5, f"ROI: {orig_w}×{orig_h} (原始)")
    
    def get_roi_rect(self):
        """获取ROI矩形"""
        return self.roi_rect
    
    def clear_roi(self):
        """清除ROI选择"""
        self.roi_rect = None
        self.start_point = None
        self.end_point = None
        self.roi_cleared.emit()  # 发送清除信号
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
