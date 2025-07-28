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
        图像处理流水线 - 修复处理顺序版本
        处理顺序：旋转 → ROI提取 → 尺寸调整（与预览显示一致）
        """
        if image is None:
            return None
            
        processed_image = image.copy()
        
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"原始图像尺寸: {processed_image.shape}")
        
        # 1. 首先应用旋转（与预览显示顺序一致）
        if rotation_angle != 0:
            processed_image = ImageProcessor.rotate_image(processed_image, rotation_angle)
            logger.debug(f"旋转后尺寸: {processed_image.shape}")
        
        # 2. 然后在旋转后的图像上提取ROI
        if roi_coords and scale_factor > 0:
            x, y, w, h = roi_coords
            
            # 将预览坐标转换为旋转后图像的实际坐标
            actual_x = int(x / scale_factor)
            actual_y = int(y / scale_factor)
            actual_w = int(w / scale_factor)
            actual_h = int(h / scale_factor)
            
            # 边界检查
            img_height, img_width = processed_image.shape[:2]
            actual_x = max(0, min(actual_x, img_width - 1))
            actual_y = max(0, min(actual_y, img_height - 1))
            actual_w = min(actual_w, img_width - actual_x)
            actual_h = min(actual_h, img_height - actual_y)
            
            logger.debug(f"ROI坐标转换: 预览({x},{y},{w},{h}) → 实际({actual_x},{actual_y},{actual_w},{actual_h})")
            
            # 提取ROI
            if actual_w > 10 and actual_h > 10:
                processed_image = processed_image[actual_y:actual_y+actual_h, 
                                                actual_x:actual_x+actual_w]
                logger.debug(f"ROI提取后尺寸: {processed_image.shape}")
        
        # 3. 最后调整到目标尺寸
        processed_image = ImageProcessor.resize_to_target(processed_image, target_size)
        logger.debug(f"最终尺寸: {processed_image.shape}")
        
        return processed_image
    
    @staticmethod
    def process_image_pipeline_wysiwyg(image, rotation_angle=0, roi_coords=None, 
                                      target_size=(240, 240), preview_size=None):
        """
        所见即所得的图像处理流水线
        直接基于预览显示的图像进行处理，确保ROI完全一致
        """
        if image is None:
            return None
        
        import logging
        logger = logging.getLogger(__name__)
        
        # 1. 先旋转图像（与预览一致）
        processed_image = image.copy()
        if rotation_angle != 0:
            processed_image = ImageProcessor.rotate_image(processed_image, rotation_angle)
        
        # 2. 如果有ROI坐标，直接在旋转后的原图上应用ROI
        # （坐标已经在get_processing_params中进行了转换）
        if roi_coords:
            x, y, w, h = roi_coords
            original_h, original_w = processed_image.shape[:2]
            
            logger.debug(f"ROI处理: 旋转后图像尺寸={original_w}x{original_h}, ROI坐标=({x},{y},{w},{h})")
            
            # 边界检查
            x = max(0, min(x, original_w - 1))
            y = max(0, min(y, original_h - 1))
            w = min(w, original_w - x)
            h = min(h, original_h - y)
            
            if w > 10 and h > 10:
                # 直接从旋转后的原图提取ROI
                roi_image = processed_image[y:y+h, x:x+w]
                logger.debug(f"ROI提取成功: 实际坐标({x},{y},{w},{h}) -> ROI尺寸{roi_image.shape}")
                processed_image = roi_image
            else:
                logger.warning(f"ROI区域太小: {w}x{h}, 使用原图")
        
        # 3. 最后调整到目标尺寸
        processed_image = ImageProcessor.resize_to_target(processed_image, target_size)
        
        return processed_image