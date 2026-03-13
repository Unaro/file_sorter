from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QLineEdit, QCheckBox, 
    QRadioButton, QButtonGroup, QTextEdit, QFileDialog,
    QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from pathlib import Path
import logging
from typing import List, Optional

from core.config_manager import ConfigManager
from core.sorter import FileSorter, SortResult
from core.types import Settings
from ui.category_editor import CategoryEditor
from ui.preview_window import PreviewWindow

class SorterThread(QThread):
    """Поток для выполнения сортировки в фоне"""
    
    finished = Signal(list)  # Signal[List[SortResult]]
    log_message = Signal(str)
    
    def __init__(
        self, 
        sorter: FileSorter, 
        source_dir: Path, 
        target_dir: Path, 
        dry_run: bool,
        preview_results: Optional[List[SortResult]] = None
    ):
        super().__init__()
        self.sorter = sorter
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.dry_run = dry_run
        self.preview_results = preview_results
    
    def run(self) -> None:
        """Выполнение сортировки"""
        if self.dry_run:
            # Обычный предпросмотр
            results = self.sorter.sort_directory(
                self.source_dir,
                self.target_dir,
                self.dry_run
            )
        else:
            # Применяем результаты предпросмотра
            if self.preview_results:
                results = self.sorter.apply_preview_results(
                    self.preview_results,
                    self.target_dir
                )
            else:
                results = self.sorter.sort_directory(
                    self.source_dir,
                    self.target_dir,
                    self.dry_run
                )
        
        self.finished.emit(results)

class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self) -> None:
        super().__init__()
        self.config_manager = ConfigManager()
        self.logger = logging.getLogger(__name__)
        
        # Для хранения результатов предпросмотра
        self.preview_results: Optional[List[SortResult]] = None
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self) -> None:
        """Инициализация интерфейса"""
        self.setWindowTitle("Сортировщик файлов")
        self.setMinimumSize(800, 600)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QVBoxLayout(central_widget)
        
        # Группа выбора директорий
        dir_group = self._create_directory_group()
        main_layout.addWidget(dir_group)
        
        # Группа настроек
        settings_group = self._create_settings_group()
        main_layout.addWidget(settings_group)
        
        # Кнопки управления
        buttons_layout = self._create_buttons_layout()
        main_layout.addLayout(buttons_layout)
        
        # Область логов
        log_group = self._create_log_group()
        main_layout.addWidget(log_group)
    
    def _create_directory_group(self) -> QGroupBox:
        """Создание группы выбора директорий"""
        group = QGroupBox("Директории")
        layout = QVBoxLayout()
        
        # Исходная директория
        source_layout = QHBoxLayout()
        source_label = QLabel("Исходная папка:")
        source_label.setMinimumWidth(120)
        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("Выберите папку для сортировки...")
        source_btn = QPushButton("Обзор...")
        source_btn.clicked.connect(self.select_source_directory)
        
        source_layout.addWidget(source_label)
        source_layout.addWidget(self.source_edit)
        source_layout.addWidget(source_btn)
        
        # Целевая директория
        target_layout = QHBoxLayout()
        target_label = QLabel("Целевая папка:")
        target_label.setMinimumWidth(120)
        self.target_edit = QLineEdit()
        self.target_edit.setPlaceholderText("Выберите папку для категорий...")
        target_btn = QPushButton("Обзор...")
        target_btn.clicked.connect(self.select_target_directory)
        
        target_layout.addWidget(target_label)
        target_layout.addWidget(self.target_edit)
        target_layout.addWidget(target_btn)
        
        layout.addLayout(source_layout)
        layout.addLayout(target_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_settings_group(self) -> QGroupBox:
        """Создание группы настроек"""
        group = QGroupBox("Настройки")
        layout = QVBoxLayout()
        
        # Чекбокс рекурсивной обработки
        self.subfolder_check = QCheckBox("Обрабатывать подпапки (рекурсивно, в конце)")
        layout.addWidget(self.subfolder_check)
        
        # Чекбокс игнорирования скрытых файлов
        self.hidden_check = QCheckBox("Игнорировать скрытые файлы")
        self.hidden_check.setChecked(True)
        layout.addWidget(self.hidden_check)
        
        # Обработка дубликатов
        duplicate_label = QLabel("Обработка дубликатов:")
        layout.addWidget(duplicate_label)
        
        self.duplicate_group = QButtonGroup()
        self.duplicate_ask_radio = QRadioButton("Спрашивать пользователя")
        self.duplicate_folder_radio = QRadioButton("Переносить в папку 'Дубликаты'")
        self.duplicate_ask_radio.setChecked(True)
        
        self.duplicate_group.addButton(self.duplicate_ask_radio)
        self.duplicate_group.addButton(self.duplicate_folder_radio)
        
        layout.addWidget(self.duplicate_ask_radio)
        layout.addWidget(self.duplicate_folder_radio)
        
        group.setLayout(layout)
        return group
    
    def _create_buttons_layout(self) -> QHBoxLayout:
        """Создание кнопок управления"""
        layout = QHBoxLayout()
        
        # Кнопка управления категориями
        self.categories_btn = QPushButton("⚙ Управление категориями")
        self.categories_btn.clicked.connect(self.open_category_editor)
        
        # Кнопка запуска (сразу открывает предпросмотр)
        self.sort_btn = QPushButton("▶ Запустить сортировку")
        self.sort_btn.clicked.connect(self.start_preview)
        self.sort_btn.setStyleSheet("QPushButton { font-weight: bold; padding: 8px 16px; }")
        
        layout.addWidget(self.categories_btn)
        layout.addStretch()
        layout.addWidget(self.sort_btn)
        
        return layout
    
    def _create_log_group(self) -> QGroupBox:
        """Создание области логов"""
        group = QGroupBox("Лог операций")
        layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        
        layout.addWidget(self.log_text)
        
        group.setLayout(layout)
        return group
    
    def select_source_directory(self) -> None:
        """Выбор исходной директории"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для сортировки",
            self.source_edit.text()
        )
        if directory:
            self.source_edit.setText(directory)
    
    def select_target_directory(self) -> None:
        """Выбор целевой директории"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для создания категорий",
            self.target_edit.text()
        )
        if directory:
            self.target_edit.setText(directory)
    
    def load_settings(self) -> None:
        """Загрузка настроек из конфигурации"""
        settings = self.config_manager.get_settings()
        
        self.source_edit.setText(str(settings.get("last_source_dir", "")))
        self.target_edit.setText(str(settings.get("last_target_dir", "")))
        self.subfolder_check.setChecked(bool(settings.get("process_subfolders", False)))
        self.hidden_check.setChecked(bool(settings.get("ignore_hidden", True)))
        
        duplicate_handling = str(settings.get("duplicate_handling", "ask"))
        if duplicate_handling == "duplicate_folder":
            self.duplicate_folder_radio.setChecked(True)
        else:
            self.duplicate_ask_radio.setChecked(True)
    
    def save_settings(self) -> None:
        """Сохранение настроек в конфигурацию"""
        duplicate_handling = "duplicate_folder" if self.duplicate_folder_radio.isChecked() else "ask"
        
        settings: Settings = {
            "last_source_dir": self.source_edit.text(),
            "last_target_dir": self.target_edit.text(),
            "process_subfolders": self.subfolder_check.isChecked(),
            "ignore_hidden": self.hidden_check.isChecked(),
            "duplicate_handling": duplicate_handling
        }
        
        self.config_manager.update_settings(settings)
    
    def open_category_editor(self) -> None:
        """Открытие редактора категорий"""
        editor = CategoryEditor(self.config_manager, self)
        editor.exec()
    
    def start_preview(self) -> None:
        """Запуск предпросмотра (первый шаг)"""
        if not self._validate_directories():
            return
        
        self.save_settings()
        self.log_text.clear()
        self.log_text.append("🔍 Запуск предпросмотра...")
        
        # Создание sorter
        sorter = self._create_sorter()
        
        # Запуск в отдельном потоке
        source_dir = Path(self.source_edit.text())
        target_dir = Path(self.target_edit.text())
        
        self.sorter_thread = SorterThread(sorter, source_dir, target_dir, dry_run=True)
        self.sorter_thread.finished.connect(self._show_preview_window)
        self.sorter_thread.start()
        
        self.sort_btn.setEnabled(False)
        self.categories_btn.setEnabled(False)
    
    def _show_preview_window(self, results: List[SortResult]) -> None:
        """Показ окна предпросмотра с результатами"""
        self.sort_btn.setEnabled(True)
        self.categories_btn.setEnabled(True)
        
        self.log_text.append(f"✓ Предпросмотр готов. Найдено файлов: {len(results)}")
        
        # Создаем окно предпросмотра
        preview = PreviewWindow(
            results,
            Path(self.source_edit.text()),
            Path(self.target_edit.text()),
            self
        )
        
        # Подключаем сигнал для получения подтвержденных результатов
        preview.results_confirmed.connect(self._start_actual_sorting)
        
        preview.exec()
    
    def _start_actual_sorting(self, confirmed_results: List[SortResult]) -> None:
        """Запуск реальной сортировки после подтверждения"""
        self.preview_results = confirmed_results
        
        self.log_text.append("\n" + "="*50)
        self.log_text.append("🚀 Начало сортировки...")
        self.log_text.append("="*50)
        
        # Запускаем реальную сортировку
        source_dir = Path(self.source_edit.text())
        target_dir = Path(self.target_edit.text())
        
        sorter = self._create_sorter()
        
        # Используем специальный метод для применения предпросмотра
        self.sorter_thread = SorterThread(
            sorter, 
            source_dir, 
            target_dir, 
            dry_run=False,
            preview_results=confirmed_results
        )
        self.sorter_thread.finished.connect(self._sorting_finished)
        self.sorter_thread.start()
        
        self.sort_btn.setEnabled(False)
        self.categories_btn.setEnabled(False)
    
    def _sorting_finished(self, results: List[SortResult]) -> None:
        """Обработка завершения сортировки"""
        self.sort_btn.setEnabled(True)
        self.categories_btn.setEnabled(True)
        
        success_count = sum(1 for r in results if r.success)
        
        self.log_text.append(f"\n{'='*50}")
        self.log_text.append(f"✅ Сортировка завершена!")
        self.log_text.append(f"Успешно обработано: {success_count} из {len(results)}")
        self.log_text.append(f"{'='*50}")
        
        QMessageBox.information(
            self,
            "Завершено",
            f"Сортировка завершена!\n\nОбработано файлов: {success_count} из {len(results)}"
        )
    
    def _validate_directories(self) -> bool:
        """Проверка корректности выбранных директорий"""
        source = self.source_edit.text()
        target = self.target_edit.text()
        
        if not source or not target:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Пожалуйста, выберите исходную и целевую директории."
            )
            return False
        
        source_path = Path(source)
        target_path = Path(target)
        
        if not source_path.exists():
            QMessageBox.warning(
                self,
                "Ошибка",
                f"Исходная директория не существует:\n{source}"
            )
            return False
        
        if not source_path.is_dir():
            QMessageBox.warning(
                self,
                "Ошибка",
                f"Исходный путь не является директорией:\n{source}"
            )
            return False
        
        return True
    
    def _create_sorter(self) -> FileSorter:
        """Создание объекта FileSorter с текущими настройками"""
        categories = self.config_manager.get_categories()
        settings: Settings = {
            "process_subfolders": self.subfolder_check.isChecked(),
            "ignore_hidden": self.hidden_check.isChecked(),
            "duplicate_handling": "duplicate_folder" if self.duplicate_folder_radio.isChecked() else "ask"
        }
        
        return FileSorter(categories, settings)

        """Создание объекта FileSorter с текущими настройками"""
        categories = self.config_manager.get_categories()
        settings: Settings = {
            "process_subfolders": self.subfolder_check.isChecked(),
            "ignore_hidden": self.hidden_check.isChecked(),
            "duplicate_handling": "duplicate_folder" if self.duplicate_folder_radio.isChecked() else "ask"
        }
        
        return FileSorter(categories, settings)