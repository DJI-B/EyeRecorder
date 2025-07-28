"""
对话框UI组件模块
包含用户信息设置等对话框
"""

import os
from PyQt5.QtWidgets import (
    QLabel, QPushButton, QLineEdit, QDialog, QVBoxLayout,
    QDialogButtonBox, QMessageBox
)
from PyQt5.QtCore import Qt


class UserInfoDialog(QDialog):
    """用户信息设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📝 用户信息设置")
        self.setFixedSize(540, 350)  # 增加高度
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint)
        self.setup_ui()
        
    def setup_ui(self):
        """设置对话框界面"""
        layout = QVBoxLayout()
        layout.setSpacing(20)  # 增加元素间距
        
        # 标题
        title = QLabel("🎯 首次使用需要设置用户信息")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
                QLabel { 
            font-size: 12pt; 
            font-weight: 600; 
            color: #495057; 
            margin-bottom: 5px;
        }
        """)
        layout.addWidget(title)
        
        # 用户名输入
        username_label = QLabel("👤 用户名:")  # 确保使用标准的emoji和文字
        username_label.setStyleSheet("QLabel { font-size: 11pt; font-weight: 600; color: #495057; }")
        layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入您的用户名")
        self.username_input.setStyleSheet(self.get_input_style())
        layout.addWidget(self.username_input)
        
        # 在邮箱标签前添加额外间距
        layout.addSpacing(10)
        
        # 邮箱输入
        email_label = QLabel("📧 邮箱:")  # 确保使用标准的emoji和文字
        email_label.setStyleSheet("QLabel { font-size: 11pt; font-weight: 600; color: #495057; }")
        layout.addWidget(email_label)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("请输入您的邮箱地址")
        self.email_input.setStyleSheet(self.get_input_style())
        layout.addWidget(self.email_input)
        
        # 在按钮前添加额外间距
        layout.addSpacing(15)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.setStyleSheet("""
            QPushButton {
                padding: 10px 25px;
                font-size: 11pt;
                font-weight: 600;
                border-radius: 6px;
                min-width: 80px;
            }
            QPushButton[text="OK"] {
                background-color: #28a745;
                color: white;
                border: none;
            }
            QPushButton[text="OK"]:hover {
                background-color: #218838;
            }
            QPushButton[text="Cancel"] {
                background-color: #6c757d;
                color: white;
                border: none;
            }
            QPushButton[text="Cancel"]:hover {
                background-color: #5a6268;
            }
        """)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def get_input_style(self):
        """获取输入框样式"""
        return """
            QLineEdit {
                border: 2px solid #e9ecef;
                border-radius: 6px;
                padding: 12px 15px;
                font-size: 11pt;
                background-color: white;
                color: #495057;
            }
            QLineEdit:focus {
                border-color: #007bff;
                background-color: #f8f9ff;
            }
        """
    
    def get_user_info(self):
        """获取用户信息"""
        return {
            'username': self.username_input.text().strip(),
            'email': self.email_input.text().strip()
        }
    
    def accept(self):
        """确认按钮处理"""
        user_info = self.get_user_info()
        if not user_info['username']:
            QMessageBox.warning(self, "⚠️ 提示", "请输入用户名！")
            return
        if not user_info['email']:
            QMessageBox.warning(self, "⚠️ 提示", "请输入邮箱地址！")
            return
        super().accept()
