import re
from pathlib import Path
from typing import List, Optional
from controllers.base_controller import BaseLauncherController
import logging

try:
    import pylnk3  # type: ignore
    HAS_PYLNK = True
except ImportError:
    HAS_PYLNK = False

class SteamController(BaseLauncherController):
    """Контроллер для Steam игр"""
    
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
    
    def scan_directory(self, path: str) -> List[str]:
        """
        Сканирует Steam директорию и возвращает названия игр
        
        Args:
            path: Путь к steamapps/common/
        
        Returns:
            Список названий папок игр
        """
        try:
            scan_path = Path(path)
            if not scan_path.exists() or not scan_path.is_dir():
                self.logger.warning(f"Путь не существует или не является директорией: {path}")
                return []
            
            # Сканируем только первый уровень
            game_folders = [
                item.name for item in scan_path.iterdir() 
                if item.is_dir()
            ]
            
            self.logger.info(f"Найдено игр Steam: {len(game_folders)}")
            return game_folders
        
        except Exception as e:
            self.logger.error(f"Ошибка сканирования Steam директории: {e}")
            return []
    
    def match_item(self, item_path: Path) -> bool:
        """
        Проверяет, является ли файл/папка Steam игрой
        
        Args:
            item_path: Путь к файлу
        
        Returns:
            True если это Steam игра
        """
        # Проверка ярлыков
        if item_path.suffix.lower() in ['.lnk', '.url']:
            app_id = self.get_identifier(item_path)
            return app_id is not None
        
        # Проверка папки на наличие steam_appid.txt
        if item_path.is_dir():
            return (item_path / "steam_appid.txt").exists()
        
        return False
    
    def get_identifier(self, item_path: Path) -> Optional[str]:
        """
        Извлекает Steam AppID из ярлыка или папки
        
        Args:
            item_path: Путь к ярлыку или папке
        
        Returns:
            AppID или None
        """
        try:
            # Парсинг .lnk файла
            if item_path.suffix.lower() == '.lnk':
                return self._parse_lnk_file(item_path)
            
            # Парсинг .url файла
            elif item_path.suffix.lower() == '.url':
                return self._parse_url_file(item_path)
            
            # Чтение steam_appid.txt из папки
            elif item_path.is_dir():
                appid_file = item_path / "steam_appid.txt"
                if appid_file.exists():
                    return appid_file.read_text().strip()
        
        except Exception as e:
            self.logger.error(f"Ошибка извлечения AppID из {item_path}: {e}")
        
        return None
    
    def _parse_lnk_file(self, lnk_path: Path) -> Optional[str]:
        """Парсинг .lnk файла для извлечения Steam AppID"""
        if not HAS_PYLNK:
            self.logger.warning("Библиотека pylnk3 не установлена")
            return None
        
        try:
            import pylnk3  # Повторный импорт внутри функции для типизации
            
            with open(lnk_path, 'rb') as f:
                lnk = pylnk3.parse(f)
                
                # Проверяем командную строку на наличие steam://
                if hasattr(lnk, 'arguments'):
                    args_value = lnk.arguments
                    if args_value is not None and isinstance(args_value, str):
                        if 'steam://' in args_value.lower():
                            match = re.search(r'steam://rungameid/(\d+)', args_value, re.IGNORECASE)
                            if match:
                                return match.group(1)
                
                # Проверяем путь к целевому файлу
                if hasattr(lnk, 'path'):
                    path_value = lnk.path
                    if path_value is not None and isinstance(path_value, str):
                        if 'steam' in path_value.lower():
                            # Пытаемся найти steam_appid.txt в целевой директории
                            target_dir = Path(path_value).parent
                            appid_file = target_dir / "steam_appid.txt"
                            if appid_file.exists():
                                return appid_file.read_text().strip()
        
        except Exception as e:
            self.logger.error(f"Ошибка парсинга .lnk файла {lnk_path}: {e}")
        
        return None
    
    def _parse_url_file(self, url_path: Path) -> Optional[str]:
        """Парсинг .url файла для извлечения Steam AppID"""
        try:
            content = url_path.read_text(encoding='utf-8')
            
            # Ищем steam://rungameid/XXXXX
            match = re.search(r'steam://rungameid/(\d+)', content, re.IGNORECASE)
            if match:
                return match.group(1)
            
            # Ищем URL вида store.steampowered.com/app/XXXXX
            match = re.search(r'store\.steampowered\.com/app/(\d+)', content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        except Exception as e:
            self.logger.error(f"Ошибка парсинга .url файла {url_path}: {e}")
        
        return None
