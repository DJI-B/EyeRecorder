"""
图像处理核心模块
处理图像旋转、ROI提取、尺寸调整等功能
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
旋转图像
        
        Args:
            image: 输入图像
            angle: 旋转角度
            
        Returns:
            旋转后的图像
        """
        if angle == 0:
            return image
            
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        
        # 计算旋转矩阵
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # 计算旋转后的边界框
        cos = np.abs(rotation_matrix[0, 0])
        sin = np.abs(rotation_matrix[0, 1])
        new_width = int((height * sin) + (width * cos))
        new_height = int((height * cos) + (width * sin))
        
        # 调整旋转矩阵的平移部分
        rotation_matrix[0, 2] += (new_width / 2) - center[0]
        rotation_matrix[1, 2] += (new_height / 2) - center[1]
        
        # 执行旋转
        rotated = cv2.warpAffine(image, rotation_matrix, (new_width, new_height), 
                                flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        
        return rotated
    
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
图像处理流水线
        
        Args:
            image: 输入图像
            rotation_angle: 旋转角度
            roi_coords: ROI坐标
            target_size: 目标尺寸
            scale_factor: 缩放因子（用于坐标转换）
            
        Returns:
            处理后的图像
        """
        processed_image = image.copy()
        
        # 1. 应用旋转
        if rotation_angle != 0:
            processed_image = ImageProcessor.rotate_image(processed_image, rotation_angle)
        
        # 2. 提取ROI区域
        if roi_coords:
            # 将预览坐标转换为实际图像坐标
            if scale_factor > 0:
                x, y, w, h = roi_coords
                scale = 1.0 / scale_factor
                actual_roi = (
                    int(x * scale),
                    int(y * scale),
                    int(w * scale),
                    int(h * scale)
                )
                processed_image = ImageProcessor.extract_roi(processed_image, actual_roi)
        
        # 3. 调整尺寸
        processed_image = ImageProcessor.resize_to_target(processed_image, target_size)
        
        return processed_image
