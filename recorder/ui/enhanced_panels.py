"""
增强版UI面板模块
包含旋转、ROI等增强功能的UI面板
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QGroupBox, QSlider, QSpinBox, QMessageBox
)
from PyQt5.QtCore import Qt
from .components import ROISelector


class RotationPanel(QGroupBox):
    """
    旋转设置面板
    提供图像旋转功能的UI控件
    """
    
    def __init__(self, parent=None):
        super().__init__("🔄 图像旋转", parent)
        self.rotation_angle = 0
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """设置UI布局"""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # 旋转角度设置
        angle_layout = QHBoxLayout()
        angle_label = QLabel("旋转角度:")
        angle_label.setStyleSheet("QLabel { font-weight: 600; }")
        angle_layout.addWidget(angle_label)
        
        # 角度滑块
        self.rotation_slider = QSlider(Qt.Horizontal)
        self.rotation_slider.setRange(-180, 180)
        self.rotation_slider.setValue(0)
        self.rotation_slider.setStyleSheet(self._get_slider_style())
        angle_layout.addWidget(self.rotation_slider)
        
        # 角度数值输入
        self.angle_spinbox = QSpinBox()
        self.angle_spinbox.setRange(-180, 180)
        self.angle_spinbox.setValue(0)
        self.angle_spinbox.setSuffix("°")
        self.angle_spinbox.setStyleSheet(self._get_spinbox_style())
        angle_layout.addWidget(self.angle_spinbox)
        
        layout.addLayout(angle_layout)
        
        # 快速旋转按钮
        quick_buttons_layout = QHBoxLayout()
        quick_buttons = [
            ("↺ -90°", -90),
            ("⟲ 0°", 0),
            ("↻ +90°", 90),
            ("↕ 180°", 180)
        ]
        
        for text, angle in quick_buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(self._get_button_style())
            btn.clicked.connect(lambda checked, a=angle: self.set_rotation_angle(a))
            quick_buttons_layout.addWidget(btn)
        
        layout.addLayout(quick_buttons_layout)
        self.setLayout(layout)
    
    def connect_signals(self):
        """连接信号"""
        self.rotation_slider.valueChanged.connect(self.on_rotation_changed)
        self.angle_spinbox.valueChanged.connect(self.on_angle_spinbox_changed)
    
    def set_rotation_angle(self, angle):
        """设置旋转角度"""
        self.rotation_angle = angle
        self.rotation_slider.setValue(angle)
        self.angle_spinbox.setValue(angle)
    
    def on_rotation_changed(self, value):
        """旋转滑块变化"""
        self.rotation_angle = value
        self.angle_spinbox.setValue(value)
    
    def on_angle_spinbox_changed(self, value):
        """角度输入框变化"""
        self.rotation_angle = value
        self.rotation_slider.setValue(value)
    
    def get_rotation_angle(self):
        """获取当前旋转角度"""
        return self.rotation_angle
    
    def _get_slider_style(self):
        """获取滑块样式"""
        return """
            QSlider::groove:horizontal {
                border: 1px solid #dee2e6;
                height: 8px;
                background: #f8f9fa;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #007bff;
                border: 2px solid #0056b3;
                width: 20px;
                margin: -7px 0;
                border-radius: 10px;
            }
            QSlider::handle:horizontal:hover {
                background: #0056b3;
            }
        """
    
    def _get_spinbox_style(self):
        """获取输入框样式"""
        return """
            QSpinBox {
                border: 2px solid #e9ecef;
                border-radius: 6px;
                padding: 8px;
                font-weight: 600;
                min-width: 60px;
            }
            QSpinBox:focus {
                border-color: #007bff;
            }
        """
    
    def _get_button_style(self):
        """获取按钮样式"""
        return """
            QPushButton {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 600;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """


class ROIPanel(QGroupBox):
    """
    ROI选择面板
    提供ROI区域选择功能的UI控件
    """
    
    def __init__(self, preview_label=None, parent=None):
        super().__init__("✂️ ROI 区域选择", parent)
        self.roi_enabled = False
        self.roi_coords = None
        self.preview_label = preview_label
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """设置UI布局"""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # ROI开关
        self.roi_checkbox = QCheckBox("启用 ROI 区域截取")
        self.roi_checkbox.setStyleSheet("""
            QCheckBox {
                font-weight: 600;
                font-size: 11pt;
                color: #495057;
            }
        """)
        layout.addWidget(self.roi_checkbox)
        
        # ROI选择器说明
        roi_label = QLabel("在预览区域拖拽选择ROI:")
        roi_label.setStyleSheet("QLabel { font-weight: 600; color: #6c757d; }")
        layout.addWidget(roi_label)
        
        # ROI操作按钮
        roi_buttons_layout = QHBoxLayout()
        
        self.roi_select_btn = QPushButton("🎯 重新选择")
        self.roi_select_btn.setStyleSheet(self._get_select_button_style())
        self.roi_select_btn.setEnabled(False)
        
        self.roi_clear_btn = QPushButton("🗑️ 清除")
        self.roi_clear_btn.setStyleSheet(self._get_clear_button_style())
        self.roi_clear_btn.setEnabled(False)
        
        roi_buttons_layout.addWidget(self.roi_select_btn)
        roi_buttons_layout.addWidget(self.roi_clear_btn)
        layout.addLayout(roi_buttons_layout)
        
        # ROI信息显示
        self.roi_info_label = QLabel("未选择ROI区域")
        self.roi_info_label.setStyleSheet("""
            QLabel {
                font-size: 10pt;
                color: #6c757d;
                background-color: #f8f9fa;
                padding: 8px;
                border-radius: 6px;
                border: 1px solid #e9ecef;
            }
        """)
        layout.addWidget(self.roi_info_label)
        
        # 输出尺寸信息
        output_info = QLabel("📐 输出尺寸: 240×240 像素")
        output_info.setStyleSheet("""
            QLabel {
                font-weight: 600;
                color: #28a745;
                background-color: #f0fff4;
                padding: 8px;
                border-radius: 6px;
                border: 1px solid #c3e6cb;
            }
        """)
        layout.addWidget(output_info)
        
        self.setLayout(layout)
    
    def connect_signals(self):
        """连接信号"""
        self.roi_checkbox.stateChanged.connect(self.on_roi_enabled_changed)
        self.roi_select_btn.clicked.connect(self.enable_roi_selection)
        self.roi_clear_btn.clicked.connect(self.clear_roi_selection)
    
    def on_roi_enabled_changed(self, state):
        """
ROI启用状态变化"""
        self.roi_enabled = (state == Qt.Checked)
        self.roi_select_btn.setEnabled(self.roi_enabled)
        self.roi_clear_btn.setEnabled(self.roi_enabled and self.roi_coords is not None)
        
        if not self.roi_enabled:
            self.clear_roi_selection()
    
    def enable_roi_selection(self):
        """启用ROI选择"""
        if self.preview_label and hasattr(self.preview_label, 'clear_roi'):
            self.preview_label.clear_roi()
        QMessageBox.information(self, "ℹ️ 提示", "请在预览区域拖拽选择ROI区域")
    
    def clear_roi_selection(self):
        """清除ROI选择"""
        self.roi_coords = None
        if self.preview_label and hasattr(self.preview_label, 'clear_roi'):
            self.preview_label.clear_roi()
        self.roi_info_label.setText("未选择ROI区域")
        self.roi_clear_btn.setEnabled(False)
    
    def update_roi_info(self, roi_rect):
        """更新ROI信息"""
        if roi_rect:
            self.roi_coords = roi_rect
            x, y, w, h = roi_rect
            self.roi_info_label.setText(f"ROI: {w}×{h} (起点: {x},{y})")
            self.roi_clear_btn.setEnabled(True)
    
    def get_roi_settings(self):
        """获取ROI设置"""
        return {
            'enabled': self.roi_enabled,
            'coords': self.roi_coords
        }
    
    def _get_select_button_style(self):
        """获取选择按钮样式"""
        return """
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #6c757d;
            }
        """
    
    def _get_clear_button_style(self):
        """获取清除按钮样式"""
        return """
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #6c757d;
            }
        """
