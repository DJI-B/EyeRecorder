"""
录制会话管理模块
管理录制会话的创建、状态跟踪和文件管理
"""

import os
import json
import zipfile
import shutil
import time
from datetime import datetime
from typing import Dict, List, Optional


class RecordingSession:
    """
录制会话管理器
负责管理单次录制会话的所有方面
    """
    
    def __init__(self, user_info: Dict, save_path: str, session_type: str = "single"):
        self.user_info = user_info
        self.save_path = save_path
        self.session_type = session_type  # "single" or "multi_stage"
        self.session_start_time = time.time()
        self.recording_count = 0
        self.current_session_folder = None
        
        # 初始化会话
        self._create_session_folder()
    
    def _create_session_folder(self):
        """创建会话文件夹"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"{self.user_info['username']}_{self.session_type}_{timestamp}"
        self.current_session_folder = os.path.join(self.save_path, folder_name)
        
        try:
            os.makedirs(self.current_session_folder, exist_ok=True)
            return True
        except Exception as e:
            print(f"创建会话文件夹失败: {e}")
            return False
    
    def save_image(self, image, processing_params: Dict = None):
        """
保存图像到会话文件夹
        
        Args:
            image: 要保存的图像
            processing_params: 处理参数字典
            
        Returns:
            保存的文件路径
        """
        if image is None or self.current_session_folder is None:
            return None
        
        try:
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
            
            # 保存为JPG格式，质量95（高质量）
            import cv2
            cv2.imwrite(filepath, image, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            # 更新计数
            self.recording_count += 1
            
            return filepath
            
        except Exception as e:
            print(f"保存图像失败: {e}")
            return None
    
    def create_session_report(self):
        """创建会话报告"""
        if not self.current_session_folder:
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
            
            return report_file
            
        except Exception as e:
            print(f"创建会话报告失败: {e}")
            return None
    
    def create_session_package(self):
        """创建会话数据包（ZIP文件）"""
        if not self.current_session_folder or not os.path.exists(self.current_session_folder):
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
            
            return zip_filepath
            
        except Exception as e:
            print(f"创建会话数据包失败: {e}")
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
多阶段录制会话管理器
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
            return
            
        for i, stage in enumerate(self.recording_stages):
            stage_folder = os.path.join(
                self.current_session_folder, 
                f"stage_{i+1}_{stage['name']}"
            )
            try:
                os.makedirs(stage_folder, exist_ok=True)
                self.stage_folders.append(stage_folder)
            except Exception as e:
                print(f"创建阶段文件夹失败: {e}")
    
    def save_stage_image(self, image, processing_params: Dict = None):
        """保存阶段图像"""
        if (image is None or 
            self.current_stage >= len(self.stage_folders) or 
            not self.stage_folders[self.current_stage]):
            return None
        
        try:
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            stage = self.recording_stages[self.current_stage]
            
            # 添加处理后缀
            suffix_parts = []
            if processing_params:
                if processing_params.get('rotation_angle', 0) != 0:
                    suffix_parts.append(f"rot{processing_params['rotation_angle']}")
                if processing_params.get('roi_enabled', False):
                    suffix_parts.append("roi")
                    
            suffix = "_" + "_".join(suffix_parts) if suffix_parts else ""
            filename = f"{stage['name']}_{timestamp}_{self.stage_recording_count:06d}{suffix}_240x240.jpg"
            filepath = os.path.join(self.stage_folders[self.current_stage], filename)
            
            # 保存图像
            import cv2
            cv2.imwrite(filepath, image, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            # 更新计数
            self.stage_recording_count += 1
            self.recording_count += 1
            
            return filepath
            
        except Exception as e:
            print(f"保存阶段图像失败: {e}")
            return None
    
    def next_stage(self):
        """进入下一阶段"""
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
            "target_count": stage['target_count'],
            "progress": f"{self.stage_recording_count}/{stage['target_count']}"
        }
    
    def create_multi_stage_summary(self):
        """创建多阶段录制汇总"""
        if not self.current_session_folder:
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
                        "target_count": stage['target_count'],
                        "actual_count": len(stage_images),
                        "interval_ms": stage['interval_ms'],
                        "folder": f"stage_{i+1}_{stage['name']}"
                    }
                    summary["stages"].append(stage_info)
            
            # 保存汇总文件
            summary_file = os.path.join(self.current_session_folder, "multi_stage_summary.json")
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            return summary_file
            
        except Exception as e:
            print(f"创建多阶段汇总失败: {e}")
            return None
