from pathlib import Path
from typing import List, Tuple
import logging

class Scanner:
    """Класс для сканирования файловой системы"""
    
    def __init__(self, ignore_hidden: bool = True):
        self.ignore_hidden = ignore_hidden
        self.logger = logging.getLogger(__name__)
    
    def scan_directory(
        self, 
        path: Path, 
        recursive: bool = False,
        exclude_dirs: List[str] | None = None
    ) -> Tuple[List[Path], List[Path]]:
        """
        Сканирует директорию и возвращает списки файлов и папок
        
        Args:
            path: Путь к директории
            recursive: Рекурсивное сканирование
            exclude_dirs: Список названий директорий для исключения
        
        Returns:
            Кортеж (список файлов, список папок)
        """
        if exclude_dirs is None:
            exclude_dirs = []
        
        files: List[Path] = []
        folders: List[Path] = []
        
        try:
            if not path.exists() or not path.is_dir():
                self.logger.error(f"Путь не существует или не является директорией: {path}")
                return files, folders
            
            # Сканирование первого уровня
            for item in path.iterdir():
                # Пропуск скрытых файлов
                if self.ignore_hidden and self._is_hidden(item):
                    continue
                
                # Пропуск исключенных директорий
                if item.is_dir() and item.name in exclude_dirs:
                    continue
                
                if item.is_file():
                    files.append(item)
                elif item.is_dir():
                    folders.append(item)
            
            # Рекурсивное сканирование подпапок
            if recursive:
                for folder in folders.copy():
                    if folder.name not in exclude_dirs:
                        sub_files, sub_folders = self.scan_directory(
                            folder, 
                            recursive=True, 
                            exclude_dirs=exclude_dirs
                        )
                        files.extend(sub_files)
                        folders.extend(sub_folders)
            
            self.logger.info(f"Сканирование завершено. Найдено файлов: {len(files)}, папок: {len(folders)}")
            
        except PermissionError as e:
            self.logger.warning(f"Нет доступа к директории: {path}")
        except Exception as e:
            self.logger.error(f"Ошибка сканирования директории {path}: {e}")
        
        return files, folders
    
    def _is_hidden(self, path: Path) -> bool:
        """
        Проверяет, является ли файл/папка скрытыми
        
        Args:
            path: Путь к файлу/папке
        
        Returns:
            True если скрытый
        """
        # Проверка по имени (начинается с точки в Unix-подобных системах)
        if path.name.startswith('.'):
            return True
        
        # Проверка атрибута скрытости в Windows
        try:
            import stat
            import os
            if os.name == 'nt':  # Windows
                import ctypes
                attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
                return bool(attrs & 2)  # FILE_ATTRIBUTE_HIDDEN
        except Exception:
            pass
        
        return False
    
    def get_system_files(self) -> List[str]:
        """
        Возвращает список системных файлов для игнорирования
        
        Returns:
            Список имен системных файлов
        """
        return [
            'desktop.ini',
            'thumbs.db',
            'Thumbs.db',
            '.DS_Store',
            '$RECYCLE.BIN',
            'System Volume Information'
        ]
