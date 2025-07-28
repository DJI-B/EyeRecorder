"""
录制会话管理模块 - 调试版
添加了详细的调试信息和错误检查
"""

import os
import json
import zipfile
import shutil
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional


class RecordingSession:
    """
    录制会话管理器 - 调试版
    负责管理单次录制会话的所有方面
    """
    
    def __init__(self, user_info: Dict, save_path: str, session_type: str = "single"):
        self.logger = logging.getLogger(__name__)
        self.user_info = user_info
        self.save_path = save_path
        self.session_type = session_type
        self.session_start_time = time.time()
        self.recording_count = 0
        self.current_session_folder = None
        
        # 调试信息
        self.logger.info(f"初始化录制会话: {session_type}")
        self.logger.info(f"用户信息: {user_info}")
        self.logger.info(f"保存路径: {save_path}")
        
        # 初始化会话
        success = self._create_session_folder()
        if not success:
            self.logger.error("创建会话文件夹失败")
        else:
            self.logger.info(f"会话文件夹创建成功: {self.current_session_folder}")
    
    def _create_session_folder(self):
        """创建会话文件夹"""
        try:
            # 检查父目录是否存在
            if not os.path.exists(self.save_path):
                self.logger.info(f"创建父目录: {self.save_path}")
                os.makedirs(self.save_path, exist_ok=True)
            
            # 检查父目录权限
            if not os.access(self.save_path, os.W_OK):
                self.logger.error(f"没有写权限: {self.save_path}")
                return False
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            folder_name = f"{self.user_info['username']}_{self.session_type}_{timestamp}"
            self.current_session_folder = os.path.join(self.save_path, folder_name)
            
            self.logger.info(f"尝试创建文件夹: {self.current_session_folder}")
            os.makedirs(self.current_session_folder, exist_ok=True)
            
            # 验证文件夹是否成功创建
            if os.path.exists(self.current_session_folder):
                self.logger.info(f"文件夹创建成功: {self.current_session_folder}")
                return True
            else:
                self.logger.error(f"文件夹创建失败: {self.current_session_folder}")
                return False
                
        except Exception as e:
            self.logger.error(f"创建会话文件夹异常: {e}")
            return False
    
    def save_image(self, image, processing_params: Dict = None):
        """
        保存图像到会话文件夹 - 调试版
        
        Args:
            image: 要保存的图像
            processing_params: 处理参数字典
            
        Returns:
            保存的文件路径
        """
        self.logger.debug(f"开始保存图像，计数: {self.recording_count}")
        
        if image is None:
            self.logger.warning("图像为空，无法保存")
            return None
            
        if self.current_session_folder is None:
            self.logger.error("会话文件夹未初始化")
            return None
        
        if not os.path.exists(self.current_session_folder):
            self.logger.error(f"会话文件夹不存在: {self.current_session_folder}")
            return None
        
        try:
            # 检查图像数据
            self.logger.debug(f"图像形状: {image.shape if hasattr(image, 'shape') else 'unknown'}")
            self.logger.debug(f"图像类型: {type(image)}")
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            
            # 根据处理参数添加后缀
            suffix_parts = []
            if processing_params:
                if processing_params.get('rotation_angle', 0) != 0:
                    suffix_parts.append(f"rot{processing_params['rotation_angle']}")
                if processing_params.get('roi_enabled', False):
                    suffix_parts.append("roi")
                    
            suffix = "_" + "_".join(suffix_parts) if suffix_parts else ""
            filename = f"img_{timestamp}_{self.recording_count:06d}{suffix}_240x240.jpg"
            filepath = os.path.join(self.current_session_folder, filename)
            
            self.logger.debug(f"保存路径: {filepath}")
            
            # 保存为JPG格式，质量100（最高质量）
            import cv2
            
            # 检查cv2.imwrite的返回值
            success = cv2.imwrite(filepath, image, [cv2.IMWRITE_JPEG_QUALITY, 100])
            
            if success:
                # 验证文件是否真的被保存
                if os.path.exists(filepath):
                    file_size = os.path.getsize(filepath)
                    self.logger.info(f"图像保存成功: {filename}, 大小: {file_size} 字节")
                    self.recording_count += 1
                    return filepath
                else:
                    self.logger.error(f"cv2.imwrite返回成功但文件不存在: {filepath}")
                    return None
            else:
                self.logger.error(f"cv2.imwrite保存失败: {filepath}")
                
                # 尝试使用替代方法保存
                try:
                    import cv2
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 100]
                    result, encimg = cv2.imencode('.jpg', image, encode_param)
                    if result:
                        encimg.tofile(filepath)
                        if os.path.exists(filepath):
                            file_size = os.path.getsize(filepath)
                            self.logger.info(f"使用替代方法保存成功: {filename}, 大小: {file_size} 字节")
                            self.recording_count += 1
                            return filepath
                        else:
                            self.logger.error(f"替代方法也失败: {filepath}")
                    else:
                        self.logger.error("图像编码失败")
                except Exception as e2:
                    self.logger.error(f"替代保存方法异常: {e2}")
                
                return None
            
        except Exception as e:
            self.logger.error(f"保存图像异常: {e}")
            import traceback
            self.logger.error(f"异常堆栈: {traceback.format_exc()}")
            return None
    
    def create_session_report(self):
        """创建会话报告"""
        if not self.current_session_folder:
            self.logger.warning("无法创建会话报告：会话文件夹不存在")
            return None
            
        try:
            report = {
                "session_info": {
                    "user": self.user_info,
                    "session_type": self.session_type,
                    "start_time": datetime.fromtimestamp(self.session_start_time).isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "duration_seconds": int(time.time() - self.session_start_time),
                    "total_images": self.recording_count,
                    "save_folder": os.path.basename(self.current_session_folder)
                },
                "files": []
            }
            
            # 添加文件列表
            if os.path.exists(self.current_session_folder):
                for filename in os.listdir(self.current_session_folder):
                    if filename.endswith('.jpg'):
                        filepath = os.path.join(self.current_session_folder, filename)
                        file_info = {
                            "filename": filename,
                            "size_bytes": os.path.getsize(filepath),
                            "created_time": datetime.fromtimestamp(
                                os.path.getctime(filepath)
                            ).isoformat()
                        }
                        report["files"].append(file_info)
            
            # 保存报告
            report_file = os.path.join(self.current_session_folder, "session_report.json")
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"会话报告创建成功: {report_file}")
            return report_file
            
        except Exception as e:
            self.logger.error(f"创建会话报告失败: {e}")
            return None
    
    def create_session_package(self):
        """创建会话数据包（ZIP文件）"""
        if not self.current_session_folder or not os.path.exists(self.current_session_folder):
            self.logger.warning("无法创建数据包：会话文件夹不存在")
            return None
            
        try:
            zip_filename = f"{os.path.basename(self.current_session_folder)}.zip"
            zip_filepath = os.path.join(os.path.dirname(self.current_session_folder), zip_filename)
            
            with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 添加所有文件到ZIP
                for root, dirs, files in os.walk(self.current_session_folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, 
                                                  os.path.dirname(self.current_session_folder))
                        zipf.write(file_path, arc_path)
            
            self.logger.info(f"数据包创建成功: {zip_filepath}")
            return zip_filepath
            
        except Exception as e:
            self.logger.error(f"创建会话数据包失败: {e}")
            return None
    
    def get_session_info(self):
        """获取会话信息"""
        return {
            "folder": self.current_session_folder,
            "count": self.recording_count,
            "duration": int(time.time() - self.session_start_time),
            "user": self.user_info,
            "type": self.session_type
        }


class MultiStageSession(RecordingSession):
    """
    多阶段录制会话管理器 - 调试版
    专门用于管理多阶段录制会话
    """
    
    def __init__(self, user_info: Dict, save_path: str, recording_stages: List[Dict]):
        super().__init__(user_info, save_path, "multi_stage")
        self.recording_stages = recording_stages
        self.current_stage = 0
        self.stage_folders = []
        self.stage_recording_count = 0
        
        # 为每个阶段创建子文件夹
        self._create_stage_folders()
    
    def _create_stage_folders(self):
        """为每个阶段创建子文件夹"""
        if not self.current_session_folder:
            self.logger.error("无法创建阶段文件夹：主会话文件夹不存在")
            return
            
        for i, stage in enumerate(self.recording_stages):
            # 使用英文名称避免路径问题
            stage_name = stage.get('name', f'stage_{i+1}')
            stage_folder = os.path.join(
                self.current_session_folder, 
                f"stage_{i+1}_{stage_name}"
            )
            try:
                self.logger.info(f"创建阶段文件夹: {stage_folder}")
                os.makedirs(stage_folder, exist_ok=True)
                
                if os.path.exists(stage_folder):
                    self.stage_folders.append(stage_folder)
                    self.logger.info(f"阶段文件夹创建成功: {stage_folder}")
                else:
                    self.logger.error(f"阶段文件夹创建失败: {stage_folder}")
                    
            except Exception as e:
                self.logger.error(f"创建阶段文件夹异常: {e}")
    
    def save_stage_image(self, image, processing_params: Dict = None):
        """保存阶段图像 - 调试版"""
        self.logger.debug(f"保存阶段图像，当前阶段: {self.current_stage}, 计数: {self.stage_recording_count}")
        
        if (image is None or 
            self.current_stage >= len(self.stage_folders) or 
            not self.stage_folders[self.current_stage]):
            self.logger.warning(f"无法保存阶段图像：图像={image is not None}, 阶段={self.current_stage}, 文件夹存在={len(self.stage_folders) > self.current_stage}")
            return None
        
        try:
            # 检查阶段文件夹是否存在
            stage_folder = self.stage_folders[self.current_stage]
            if not os.path.exists(stage_folder):
                self.logger.error(f"阶段文件夹不存在: {stage_folder}")
                return None
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            stage = self.recording_stages[self.current_stage]
            
            # 使用英文名称避免路径问题
            stage_name = stage.get('name', f'stage_{self.current_stage+1}')
            
            # 添加处理后缀
            suffix_parts = []
            if processing_params:
                if processing_params.get('rotation_angle', 0) != 0:
                    suffix_parts.append(f"rot{processing_params['rotation_angle']}")
                if processing_params.get('roi_enabled', False):
                    suffix_parts.append("roi")
                    
            suffix = "_" + "_".join(suffix_parts) if suffix_parts else ""
            filename = f"{stage_name}_{timestamp}_{self.stage_recording_count:06d}{suffix}_240x240.jpg"
            filepath = os.path.join(stage_folder, filename)
            
            self.logger.debug(f"阶段图像保存路径: {filepath}")
            
            # 使用cv2.imencode方法避免中文路径问题
            import cv2
            try:
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 100]
                result, encimg = cv2.imencode('.jpg', image, encode_param)
                if result:
                    encimg.tofile(filepath)
                    if os.path.exists(filepath):
                        file_size = os.path.getsize(filepath)
                        self.logger.info(f"阶段图像保存成功: {filename}, 大小: {file_size} 字节")
                        
                        # 更新计数
                        self.stage_recording_count += 1
                        self.recording_count += 1
                        
                        return filepath
                    else:
                        self.logger.error(f"图像编码保存失败: {filepath}")
                else:
                    self.logger.error("图像编码失败")
            except Exception as encode_error:
                self.logger.error(f"图像编码异常: {encode_error}")
            
            # 如果imencode失败，尝试cv2.imwrite（仅用于调试）
            success = cv2.imwrite(filepath, image, [cv2.IMWRITE_JPEG_QUALITY, 100])
            
            if success and os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                self.logger.info(f"阶段图像cv2.imwrite保存成功: {filename}, 大小: {file_size} 字节")
                
                # 更新计数
                self.stage_recording_count += 1
                self.recording_count += 1
                
                return filepath
            else:
                self.logger.error(f"所有保存方法都失败: {filepath}")
                return None
            
        except Exception as e:
            self.logger.error(f"保存阶段图像异常: {e}")
            import traceback
            self.logger.error(f"异常堆栈: {traceback.format_exc()}")
            return None
    
    def next_stage(self):
        """进入下一阶段"""
        self.logger.info(f"从阶段 {self.current_stage} 切换到阶段 {self.current_stage + 1}")
        self.current_stage += 1
        self.stage_recording_count = 0
        return self.current_stage < len(self.recording_stages)
    
    def get_current_stage_info(self):
        """获取当前阶段信息"""
        if self.current_stage >= len(self.recording_stages):
            return None
            
        stage = self.recording_stages[self.current_stage]
        return {
            "stage_number": self.current_stage + 1,
            "stage_name": stage['name'],
            "description": stage['description'],
            "current_count": self.stage_recording_count,
            "duration_seconds": stage.get('duration_seconds', 5),
            "progress": f"{self.stage_recording_count} 张图像"
        }
    
    def create_multi_stage_summary(self):
        """创建多阶段录制汇总"""
        if not self.current_session_folder:
            self.logger.warning("无法创建多阶段汇总：会话文件夹不存在")
            return None
            
        try:
            summary = {
                "recording_info": {
                    "user": self.user_info,
                    "timestamp": datetime.now().isoformat(),
                    "total_images": self.recording_count,
                    "total_duration": int(time.time() - self.session_start_time),
                    "recording_type": "multi_stage"
                },
                "stages": []
            }
            
            # 统计各阶段信息
            for i, stage in enumerate(self.recording_stages):
                if i < len(self.stage_folders):
                    stage_folder = self.stage_folders[i]
                    stage_images = [f for f in os.listdir(stage_folder) 
                                  if f.endswith('.jpg')] if os.path.exists(stage_folder) else []
                    
                    stage_info = {
                        "stage_number": i + 1,
                        "stage_name": stage['name'],
                        "description": stage['description'],
                        "duration_seconds": stage.get('duration_seconds', 5),
                        "actual_count": len(stage_images),
                        "interval_ms": stage['interval_ms'],
                        "folder": f"stage_{i+1}_{stage['name']}"
                    }
                    summary["stages"].append(stage_info)
                    self.logger.info(f"阶段 {i+1} 统计: {len(stage_images)} 张图像")
            
            # 保存汇总文件
            summary_file = os.path.join(self.current_session_folder, "multi_stage_summary.json")
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"多阶段汇总创建成功: {summary_file}")
            return summary_file
            
        except Exception as e:
            self.logger.error(f"创建多阶段汇总失败: {e}")
            return None