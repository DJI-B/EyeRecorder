"""
图像处理核心模块 - 修复版
处理图像旋转、ROI提取、尺寸调整等功能
修复了ROI坐标转换和旋转处理问题
"""

import cv2
import numpy as np


class ImageProcessor:
    """
    图像处理器
    负责各种图像处理操作
    """
    
    @staticmethod
    def rotate_image(image, angle):
        """
        平滑旋转图像 - 避免边缘撕裂
        """
        if angle == 0:
            return image
            
        height, width = image.shape[:2]
        
       
        center = (width // 2, height // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        cos = np.abs(rotation_matrix[0, 0])
        sin = np.abs(rotation_matrix[0, 1])
        new_width = int((height * sin) + (width * cos))
        new_height = int((height * cos) + (width * sin))
        
        rotation_matrix[0, 2] += (new_width / 2) - center[0]
        rotation_matrix[1, 2] += (new_height / 2) - center[1]
        
        return cv2.warpAffine(
            image, 
            rotation_matrix, 
            (new_width, new_height),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0)
        )
    
    @staticmethod
    def extract_roi(image, roi_rect):
        """
        提取ROI区域
        
        Args:
            image: 输入图像
            roi_rect: ROI矩形 (x, y, w, h)
            
        Returns:
            提取的ROI图像
        """
        if roi_rect is None:
            return image
            
        x, y, w, h = roi_rect
        
        # 确保ROI坐标在图像范围内
        height, width = image.shape[:2]
        x = max(0, min(x, width - 1))
        y = max(0, min(y, height - 1))
        w = min(w, width - x)
        h = min(h, height - y)
        
        if w <= 0 or h <= 0:
            return image
            
        return image[y:y+h, x:x+w]
    
    @staticmethod
    def resize_to_target(image, target_size=(240, 240)):
        """
        调整图像尺寸到目标尺寸
        
        Args:
            image: 输入图像
            target_size: 目标尺寸 (width, height)
            
        Returns:
            调整尺寸后的图像
        """
        return cv2.resize(image, target_size, interpolation=cv2.INTER_AREA)
    
    @staticmethod
    def process_image_pipeline(image, rotation_angle=0, roi_coords=None, 
                             target_size=(240, 240), scale_factor=1.0):
        """
        图像处理流水线 - 修复版
        
        Args:
            image: 输入图像
            rotation_angle: 旋转角度
            roi_coords: ROI坐标 (预览坐标系: x, y, w, h)
            target_size: 目标尺寸 (width, height)
            scale_factor: 缩放因子（预览到实际图像的比例）
            
        Returns:
            处理后的图像
        """
        if image is None:
            return None
            
        processed_image = image.copy()
        
        # 1. 首先提取ROI区域（在原始图像上操作）
        if roi_coords and scale_factor > 0:
            # 将预览坐标转换为实际图像坐标
            x, y, w, h = roi_coords
            
            # 计算实际坐标（逆向缩放）
            actual_x = int(x / scale_factor)
            actual_y = int(y / scale_factor)
            actual_w = int(w / scale_factor)
            actual_h = int(h / scale_factor)
            
            # 确保坐标在有效范围内
            img_height, img_width = processed_image.shape[:2]
            actual_x = max(0, min(actual_x, img_width - 1))
            actual_y = max(0, min(actual_y, img_height - 1))
            actual_w = min(actual_w, img_width - actual_x)
            actual_h = min(actual_h, img_height - actual_y)
            
            # 只有当ROI有效时才提取
            if actual_w > 0 and actual_h > 0:
                actual_roi = (actual_x, actual_y, actual_w, actual_h)
                processed_image = ImageProcessor.extract_roi(processed_image, actual_roi)
        
        # 2. 应用旋转（在ROI提取后）
        if rotation_angle != 0:
            processed_image = ImageProcessor.rotate_image(processed_image, rotation_angle)
        
        # 3. 调整尺寸到目标大小
        processed_image = ImageProcessor.resize_to_target(processed_image, target_size)
        
        return processed_image