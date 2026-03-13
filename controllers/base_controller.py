from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

class BaseLauncherController(ABC):
    """Абстрактный класс для контроллеров лаунчеров"""
    
    @abstractmethod
    def scan_directory(self, path: str) -> List[str]:
        """
        Сканирует директорию и возвращает список элементов
        
        Args:
            path: Путь к директории для сканирования
        
        Returns:
            Список названий найденных элементов
        """
        pass
    
    @abstractmethod
    def match_item(self, item_path: Path) -> bool:
        """
        Проверяет, соответствует ли элемент этому контроллеру
        
        Args:
            item_path: Путь к файлу/папке
        
        Returns:
            True если элемент соответствует контроллеру
        """
        pass
    
    @abstractmethod
    def get_identifier(self, item_path: Path) -> Optional[str]:
        """
        Извлекает уникальный идентификатор (AppID, game ID и т.д.)
        
        Args:
            item_path: Путь к файлу/папке
        
        Returns:
            Идентификатор или None
        """
        pass