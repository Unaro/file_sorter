from typing import Dict, List, Union, TypedDict, Optional

# Типы для значений в конфигурации
ConfigValue = Union[str, int, bool, List[str], Dict[str, Union[str, int, bool, List[str]]]]

class NameDatabaseRules(TypedDict, total=False):
    """Правила базы данных имен"""
    enabled: bool
    algorithm: str
    items: List[str]

class ControllerConfig(TypedDict, total=False):
    """Конфигурация контроллера"""
    check_appid: bool

class ControllerRules(TypedDict, total=False):
    """Правила контроллера"""
    enabled: bool
    type: str
    config: ControllerConfig

class ExtensionRules(TypedDict, total=False):
    """Правила расширений"""
    enabled: bool
    list: List[str]

class CategoryRules(TypedDict, total=False):
    """Все правила категории"""
    name_database: NameDatabaseRules
    controller: ControllerRules
    extensions: ExtensionRules

class CategoryDict(TypedDict, total=False):
    """Структура категории"""
    name: str
    enabled: bool
    priority: int
    rules: CategoryRules

class Settings(TypedDict, total=False):
    """Настройки приложения"""
    last_source_dir: str
    last_target_dir: str
    process_subfolders: bool
    duplicate_handling: str
    ignore_hidden: bool

class Config(TypedDict):
    """Полная конфигурация"""
    version: str
    settings: Settings
    categories: List[CategoryDict]
