from pathlib import Path
from typing import List, Optional, Tuple
import logging
from core.scanner import Scanner
from core.matcher import Matcher
from core.types import CategoryDict, CategoryRules, Settings
from controllers.base_controller import BaseLauncherController
from controllers.steam_controller import SteamController
from utils.file_operations import FileOperations

class CategoryRule:
    """Класс для хранения правила категории"""
    
    def __init__(self, category_data: CategoryDict):
        self.name: str = category_data.get("name", "")
        self.enabled: bool = category_data.get("enabled", True)
        self.priority: int = category_data.get("priority", 999)
        
        rules = category_data.get("rules", {})
        self.rules: CategoryRules = rules if rules else {}

class SortResult:
    """Результат сортировки файла"""
    
    def __init__(
        self, 
        source: Path, 
        category: str, 
        rule_type: str,
        success: bool = False,
        destination: Optional[Path] = None
    ):
        self.source = source
        self.category = category
        self.rule_type = rule_type
        self.success = success
        self.destination = destination

class FileSorter:
    """Основной класс для сортировки файлов"""
    
    def __init__(self, categories: List[CategoryDict], settings: Settings):
        self.logger = logging.getLogger(__name__)
        self.categories = [CategoryRule(cat) for cat in categories]
        self.categories.sort(key=lambda x: x.priority)
        
        self.settings = settings
        self.scanner = Scanner(ignore_hidden=settings.get("ignore_hidden", True))
        self.file_ops = FileOperations()
        self.matcher = Matcher()
        
        # Инициализация контроллеров
        self.controllers: dict[str, BaseLauncherController] = {
            "steam": SteamController()
        }
        
        # Статистика
        self.stats = {
            "total_files": 0,
            "processed": 0,
            "skipped": 0,
            "errors": 0
        }
    
    def categorize_item(self, item: Path) -> Tuple[Optional[str], str]:
        """
        Определяет категорию для файла/папки
        
        Args:
            item: Путь к файлу/папке
        
        Returns:
            Кортеж (название категории или None, тип правила)
        """
        filename = item.name
        self.logger.debug(f"Категоризация: {filename}")
        
        for category in self.categories:
            if not category.enabled:
                self.logger.debug(f"  - Категория '{category.name}' отключена, пропуск")
                continue
            
            rules = category.rules
            
            # Приоритет 1: Проверка по базе данных имен
            name_db_rules = rules.get("name_database")
            if name_db_rules and name_db_rules.get("enabled"):
                items_list = name_db_rules.get("items", [])
                algorithm = name_db_rules.get("algorithm", "exact")
                
                self.logger.debug(f"  - Проверка '{category.name}' по базе данных имен (алгоритм: {algorithm})")
                
                if self.matcher.match_by_name(filename, items_list, algorithm):
                    self.logger.info(f"✓ '{filename}' → '{category.name}' (база данных имен)")
                    return category.name, "name_database"
            
            # Приоритет 2: Проверка контроллером
            controller_rules = rules.get("controller")
            if controller_rules and controller_rules.get("enabled"):
                controller_type = controller_rules.get("type")
                
                self.logger.debug(f"  - Проверка '{category.name}' контроллером {controller_type}")
                
                if controller_type and controller_type in self.controllers:
                    controller = self.controllers[controller_type]
                    if controller.match_item(item):
                        self.logger.info(f"✓ '{filename}' → '{category.name}' (контроллер {controller_type})")
                        return category.name, f"controller_{controller_type}"
            
            # Приоритет 3: Проверка по расширению
            ext_rules = rules.get("extensions")
            if ext_rules and ext_rules.get("enabled"):
                ext_list = ext_rules.get("list", [])
                
                self.logger.debug(f"  - Проверка '{category.name}' по расширению")
                
                if self.matcher.match_by_extension(filename, ext_list):
                    self.logger.info(f"✓ '{filename}' → '{category.name}' (расширение)")
                    return category.name, "extension"
        
        self.logger.warning(f"✗ '{filename}' не подошел ни под одну категорию → 'Прочее'")
        return None, "none"
    
    def sort_directory(
        self,
        source_dir: Path,
        target_dir: Path,
        dry_run: bool = False
    ) -> List[SortResult]:
        """
        Сортирует файлы в директории
        
        Args:
            source_dir: Исходная директория
            target_dir: Целевая директория для создания категорий
            dry_run: Режим предпросмотра без реального перемещения
        
        Returns:
            Список результатов сортировки
        """
        results: List[SortResult] = []
        
        self.logger.info(f"Начало сортировки: {source_dir}")
        self.logger.info(f"Целевая директория: {target_dir}")
        self.logger.info(f"Режим: {'Предпросмотр' if dry_run else 'Сортировка'}")
        
        # Получаем список категорий для исключения из сканирования
        category_names = [cat.name for cat in self.categories]
        
        # Сканирование
        process_subfolders = self.settings.get("process_subfolders", False)
        files, folders = self.scanner.scan_directory(
            source_dir,
            recursive=False,
            exclude_dirs=category_names
        )
        
        all_items = files + folders
        self.stats["total_files"] = len(all_items)
        
        self.logger.info(f"Найдено элементов: {len(all_items)}")
        
        # Обработка файлов и папок
        for item in all_items:
            result = self._process_item(item, target_dir, dry_run)
            results.append(result)
        
        # Рекурсивная обработка подпапок (в конце)
        if process_subfolders and not dry_run:
            self.logger.info("Начало рекурсивной обработки подпапок...")
            for folder in folders:
                if folder.name not in category_names:
                    sub_results = self.sort_directory(folder, target_dir, dry_run=False)
                    results.extend(sub_results)
        
        self.logger.info(f"Сортировка завершена. Обработано: {self.stats['processed']}, "
                        f"Пропущено: {self.stats['skipped']}, Ошибок: {self.stats['errors']}")
        
        return results
    
    def _process_item(
        self, 
        item: Path, 
        target_dir: Path, 
        dry_run: bool
    ) -> SortResult:
        """
        Обрабатывает один элемент (файл или папку)
        
        Args:
            item: Путь к элементу
            target_dir: Целевая директория
            dry_run: Режим предпросмотра
        
        Returns:
            Результат обработки
        """
        # Пропуск системных файлов
        if item.name in self.scanner.get_system_files():
            self.stats["skipped"] += 1
            return SortResult(item, "Пропущено", "system_file")
        
        # Определение категории
        category, rule_type = self.categorize_item(item)
        
        if category is None:
            category = "Прочее"
            rule_type = "default"
        
        # В режиме предпросмотра не перемещаем файлы
        if dry_run:
            return SortResult(item, category, rule_type, success=True)
        
        # Создание папки категории
        category_path = self.file_ops.create_category_folder(target_dir, category)
        if category_path is None:
            self.stats["errors"] += 1
            return SortResult(item, category, rule_type, success=False)
        
        # Обработка дубликатов
        duplicate_handling = self.settings.get("duplicate_handling", "ask")
        destination = category_path / item.name
        
        if destination.exists():
            if duplicate_handling == "ask":
                self.logger.warning(f"Дубликат обнаружен: {item.name}")
                self.stats["skipped"] += 1
                return SortResult(item, "Дубликаты", "duplicate", success=False)
            
            elif duplicate_handling == "duplicate_folder":
                category_path = self.file_ops.create_category_folder(target_dir, "Дубликаты")
                if category_path is None:
                    self.stats["errors"] += 1
                    return SortResult(item, category, rule_type, success=False)
        
        # Перемещение файла
        success, final_path = self.file_ops.move_item(item, category_path, duplicate_handling)
        
        if success:
            self.stats["processed"] += 1
        else:
            self.stats["errors"] += 1
        
        return SortResult(item, category, rule_type, success=success, destination=final_path)

    def apply_preview_results(
        self,
        preview_results: List[SortResult],
        target_dir: Path
    ) -> List[SortResult]:
        """
        Применяет результаты предпросмотра (с учетом изменений пользователя)
        
        Args:
            preview_results: Результаты из предпросмотра
            target_dir: Целевая директория
        
        Returns:
            Список результатов сортировки
        """
        self.logger.info("Применение результатов предпросмотра...")
        
        final_results: List[SortResult] = []
        
        for preview_result in preview_results:
            # Используем категорию из предпросмотра (возможно измененную пользователем)
            category = preview_result.category
            
            # Создание папки категории
            category_path = self.file_ops.create_category_folder(target_dir, category)
            if category_path is None:
                self.stats["errors"] += 1
                final_results.append(SortResult(
                    preview_result.source,
                    category,
                    preview_result.rule_type,
                    success=False
                ))
                continue
            
            # Обработка дубликатов
            duplicate_handling = self.settings.get("duplicate_handling", "ask")
            destination = category_path / preview_result.source.name
            
            if destination.exists():
                if duplicate_handling == "duplicate_folder":
                    category_path = self.file_ops.create_category_folder(target_dir, "Дубликаты")
                    if category_path is None:
                        self.stats["errors"] += 1
                        final_results.append(SortResult(
                            preview_result.source,
                            category,
                            preview_result.rule_type,
                            success=False
                        ))
                        continue
            
            # Перемещение файла
            success, final_path = self.file_ops.move_item(
                preview_result.source,
                category_path,
                duplicate_handling
            )
            
            if success:
                self.stats["processed"] += 1
            else:
                self.stats["errors"] += 1
            
            final_results.append(SortResult(
                preview_result.source,
                category,
                preview_result.rule_type,
                success=success,
                destination=final_path
            ))
        
        self.logger.info(f"Применение завершено. Успешно: {self.stats['processed']}, Ошибок: {self.stats['errors']}")
        
        return final_results
