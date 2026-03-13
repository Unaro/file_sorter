import json
from pathlib import Path
from typing import List, Optional
from core.types import Config, Settings, CategoryDict

class ConfigManager:
    """Управление конфигурацией приложения"""
    
    DEFAULT_CONFIG: Config = {
        "version": "1.0",
        "settings": {
            "last_source_dir": "",
            "last_target_dir": "",
            "process_subfolders": False,
            "duplicate_handling": "ask",
            "ignore_hidden": True
        },
        "categories": [
            {
                "name": "Steam игры",
                "enabled": True,
                "priority": 1,
                "rules": {
                    "name_database": {
                        "enabled": True,
                        "algorithm": "partial",
                        "items": []
                    },
                    "controller": {
                        "enabled": True,
                        "type": "steam",
                        "config": {"check_appid": True}
                    },
                    "extensions": {
                        "enabled": True,
                        "list": [".lnk", ".url"]
                    }
                }
            },
            # ... остальные категории как раньше
            {
                "name": "Программы",
                "enabled": True,
                "priority": 2,
                "rules": {
                    "name_database": {"enabled": False, "algorithm": "exact", "items": []},
                    "controller": {"enabled": False},
                    "extensions": {"enabled": True, "list": [".exe", ".msi", ".lnk"]}
                }
            },
            {
                "name": "Документы",
                "enabled": True,
                "priority": 3,
                "rules": {
                    "extensions": {"enabled": True, "list": [".doc", ".docx", ".odt", ".rtf", ".pdf"]}
                }
            },
            {
                "name": "Таблицы",
                "enabled": True,
                "priority": 4,
                "rules": {
                    "extensions": {"enabled": True, "list": [".xls", ".xlsx", ".ods", ".csv"]}
                }
            },
            {
                "name": "Текстовые файлы",
                "enabled": True,
                "priority": 5,
                "rules": {
                    "extensions": {"enabled": True, "list": [".txt", ".log"]}
                }
            },
            {
                "name": "Markdown",
                "enabled": True,
                "priority": 6,
                "rules": {
                    "extensions": {"enabled": True, "list": [".md", ".markdown"]}
                }
            },
            {
                "name": "Изображения",
                "enabled": True,
                "priority": 7,
                "rules": {
                    "extensions": {"enabled": True, "list": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico"]}
                }
            },
            {
                "name": "Видео",
                "enabled": True,
                "priority": 8,
                "rules": {
                    "extensions": {"enabled": True, "list": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"]}
                }
            },
            {
                "name": "Аудио",
                "enabled": True,
                "priority": 9,
                "rules": {
                    "extensions": {"enabled": True, "list": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"]}
                }
            },
            {
                "name": "Архивы",
                "enabled": True,
                "priority": 10,
                "rules": {
                    "extensions": {"enabled": True, "list": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".iso"]}
                }
            },
            {
                "name": "Код",
                "enabled": True,
                "priority": 11,
                "rules": {
                    "extensions": {"enabled": True, "list": [".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".json", ".xml", ".sql", ".java", ".cpp", ".c", ".cs", ".php", ".rb", ".go", ".rs"]}
                }
            }
        ]
    }
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
    
    def load_config(self) -> Config:
        """Загрузка конфигурации из файла"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config: Config = json.load(f)
                    return loaded_config
            except Exception as e:
                print(f"Ошибка загрузки конфигурации: {e}")
                return self.DEFAULT_CONFIG.copy()  # type: ignore
        else:
            self.save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()  # type: ignore
    
    def save_config(self, config: Optional[Config] = None) -> None:
        """Сохранение конфигурации в файл"""
        config_to_save = config if config is not None else self.config
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
    
    def get_settings(self) -> Settings:
        """Получить настройки"""
        return self.config["settings"]
    
    def update_settings(self, settings: Settings) -> None:
        """Обновить настройки"""
        self.config["settings"].update(settings)
        self.save_config()
    
    def get_categories(self) -> List[CategoryDict]:
        """Получить список категорий"""
        return self.config["categories"]
    
    def update_categories(self, categories: List[CategoryDict]) -> None:
        """Обновить категории"""
        self.config["categories"] = categories
        self.save_config()
    
    def add_category(self, category: CategoryDict) -> None:
        """Добавить новую категорию"""
        self.config["categories"].append(category)
        self.save_config()
    
    def remove_category(self, index: int) -> None:
        """Удалить категорию по индексу"""
        if 0 <= index < len(self.config["categories"]):
            del self.config["categories"][index]
            self.save_config()
