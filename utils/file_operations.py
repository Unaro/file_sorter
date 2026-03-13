from pathlib import Path
from typing import Optional, Tuple
import shutil
import logging

class FileOperations:
    """Класс для операций с файлами"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def move_item(
        self, 
        source: Path, 
        destination_dir: Path,
        handle_duplicate: str = "ask"
    ) -> Tuple[bool, Optional[Path]]:
        """
        Перемещает файл или папку в целевую директорию
        
        Args:
            source: Исходный путь
            destination_dir: Целевая директория
            handle_duplicate: Как обрабатывать дубликаты ("ask", "duplicate_folder", "rename", "skip")
        
        Returns:
            Кортеж (успех операции, итоговый путь или None)
        """
        try:
            # Создание целевой директории если не существует
            destination_dir.mkdir(parents=True, exist_ok=True)
            
            # Целевой путь
            destination = destination_dir / source.name
            
            # Проверка существования файла
            if destination.exists():
                if handle_duplicate == "skip":
                    self.logger.info(f"Пропущен (уже существует): {source.name}")
                    return False, None
                
                elif handle_duplicate == "rename":
                    destination = self._get_unique_path(destination)
                
                elif handle_duplicate == "duplicate_folder":
                    # Перемещение в папку "Дубликаты" будет обработано выше в sorter
                    return False, None
                
                # "ask" обрабатывается в GUI
            
            # Перемещение
            shutil.move(str(source), str(destination))
            self.logger.info(f"Перемещен: {source.name} → {destination.relative_to(destination.parent.parent)}")
            return True, destination
        
        except PermissionError:
            self.logger.error(f"Нет прав доступа для перемещения: {source}")
            return False, None
        except Exception as e:
            self.logger.error(f"Ошибка перемещения {source}: {e}")
            return False, None
    
    def _get_unique_path(self, path: Path) -> Path:
        """
        Генерирует уникальное имя файла, добавляя (1), (2) и т.д.
        
        Args:
            path: Исходный путь
        
        Returns:
            Уникальный путь
        """
        if not path.exists():
            return path
        
        counter = 1
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        
        while True:
            new_name = f"{stem} ({counter}){suffix}"
            new_path = parent / new_name
            
            if not new_path.exists():
                return new_path
            
            counter += 1
    
    def create_category_folder(self, base_path: Path, category_name: str) -> Optional[Path]:
        """
        Создает папку для категории
        
        Args:
            base_path: Базовый путь
            category_name: Название категории
        
        Returns:
            Путь к созданной папке или None при ошибке
        """
        try:
            category_path = base_path / category_name
            category_path.mkdir(parents=True, exist_ok=True)
            return category_path
        except Exception as e:
            self.logger.error(f"Ошибка создания папки категории {category_name}: {e}")
            return None
