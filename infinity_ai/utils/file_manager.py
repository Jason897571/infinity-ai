"""
文件管理工具
"""
import json
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Union
from .logger import get_logger


class FileManager:
    """文件管理器"""

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.logger = get_logger("file_manager")

    def read_file(self, file_path: Union[str, Path], encoding: str = 'utf-8') -> Optional[str]:
        """读取文件内容"""
        path = self.root_path / file_path if isinstance(file_path, str) else file_path

        if not path.exists():
            self.logger.warning(f"File not found: {path}")
            return None

        try:
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Failed to read file {path}: {e}")
            return None

    def write_file(
        self,
        file_path: Union[str, Path],
        content: str,
        encoding: str = 'utf-8',
        backup: bool = False
    ) -> bool:
        """写入文件"""
        path = self.root_path / file_path if isinstance(file_path, str) else file_path

        try:
            # 创建父目录
            path.parent.mkdir(parents=True, exist_ok=True)

            # 备份原文件
            if backup and path.exists():
                backup_path = path.with_suffix(path.suffix + '.backup')
                shutil.copy2(path, backup_path)
                self.logger.info(f"Backup created: {backup_path}")

            # 写入新内容
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)

            self.logger.info(f"File written: {path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to write file {path}: {e}")
            return False

    def read_json(self, file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """读取JSON文件"""
        content = self.read_file(file_path)
        if content is None:
            return None

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON from {file_path}: {e}")
            return None

    def write_json(
        self,
        file_path: Union[str, Path],
        data: Dict[str, Any],
        indent: int = 2,
        ensure_ascii: bool = False,
        backup: bool = False
    ) -> bool:
        """写入JSON文件"""
        try:
            content = json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
            return self.write_file(file_path, content, backup=backup)
        except Exception as e:
            self.logger.error(f"Failed to serialize JSON for {file_path}: {e}")
            return False

    def append_to_file(self, file_path: Union[str, Path], content: str) -> bool:
        """追加内容到文件"""
        path = self.root_path / file_path if isinstance(file_path, str) else file_path

        try:
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, 'a', encoding='utf-8') as f:
                f.write(content)

            self.logger.info(f"Content appended to: {path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to append to file {path}: {e}")
            return False

    def file_exists(self, file_path: Union[str, Path]) -> bool:
        """检查文件是否存在"""
        path = self.root_path / file_path if isinstance(file_path, str) else file_path
        return path.exists()

    def delete_file(self, file_path: Union[str, Path]) -> bool:
        """删除文件"""
        path = self.root_path / file_path if isinstance(file_path, str) else file_path

        if not path.exists():
            self.logger.warning(f"File not found, cannot delete: {path}")
            return False

        try:
            path.unlink()
            self.logger.info(f"File deleted: {path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete file {path}: {e}")
            return False

    def copy_file(self, src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """复制文件"""
        src_path = self.root_path / src if isinstance(src, str) else src
        dst_path = self.root_path / dst if isinstance(dst, str) else dst

        try:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
            self.logger.info(f"File copied: {src_path} -> {dst_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to copy file: {e}")
            return False

    def create_directory(self, dir_path: Union[str, Path]) -> bool:
        """创建目录"""
        path = self.root_path / dir_path if isinstance(dir_path, str) else dir_path

        try:
            path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Directory created: {path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create directory {path}: {e}")
            return False

    def list_files(self, dir_path: Union[str, Path], pattern: str = "*") -> list:
        """列出目录中的文件"""
        path = self.root_path / dir_path if isinstance(dir_path, str) else dir_path

        if not path.exists():
            return []

        return [str(p.relative_to(self.root_path)) for p in path.glob(pattern)]