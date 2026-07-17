"""
工具函数 - 文件管理、通用工具
"""
import os
import uuid
from pathlib import Path

from ..config import settings


class FileManager:
    """文件管理器 - 处理上传文件的存储和读取"""

    @staticmethod
    def save_upload(file_bytes: bytes, original_filename: str) -> str:
        """保存上传文件，返回存储路径"""
        upload_dir = settings.UPLOAD_DIR
        upload_dir.mkdir(parents=True, exist_ok=True)
        ext = Path(original_filename).suffix
        unique_name = f"{uuid.uuid4().hex}{ext}"
        file_path = upload_dir / unique_name
        with open(file_path, 'wb') as f:
            f.write(file_bytes)
        return str(file_path)

    @staticmethod
    def read_file(file_path: str) -> bytes:
        """读取文件内容"""
        with open(file_path, 'rb') as f:
            return f.read()

    @staticmethod
    def delete_file(file_path: str) -> bool:
        """删除文件"""
        try:
            os.remove(file_path)
            return True
        except OSError:
            return False
