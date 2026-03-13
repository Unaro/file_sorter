from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QGroupBox, QLabel,
    QLineEdit, QCheckBox, QComboBox, QTextEdit,
    QMessageBox, QFileDialog, QSpinBox, QWidget
)
from PySide6.QtCore import Qt
from typing import Dict, List, Optional
from pathlib import Path

from core.config_manager import ConfigManager
from core.types import CategoryDict
from controllers.steam_controller import SteamController

class CategoryEditor(QDialog):
    """Редактор категорий"""
    
    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.categories = self.config_manager.get_categories()
        self.current_index: int = -1
        
        self.init_ui()
        self.load_categories()
    
    def init_ui(self) -> None:
        """Инициализация интерфейса"""
        self.setWindowTitle("Управление категориями")
        self.setMinimumSize(900, 600)
        
        main_layout = QHBoxLayout(self)
        
        # Левая панель - список категорий
        left_panel = self._create_category_list_panel()
        main_layout.addWidget(left_panel, 1)
        
        # Правая панель - редактирование
        right_panel = self._create_editor_panel()
        main_layout.addWidget(right_panel, 2)
    
    def _create_category_list_panel(self) -> QGroupBox:
        """Создание панели списка категорий"""
        group = QGroupBox("Категории")
        layout = QVBoxLayout()
        
        # Список категорий
        self.category_list = QListWidget()
        self.category_list.currentRowChanged.connect(self.on_category_selected)
        layout.addWidget(self.category_list)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Добавить")
        self.add_btn.clicked.connect(self.add_category)
        
        self.remove_btn = QPushButton("Удалить")
        self.remove_btn.clicked.connect(self.remove_category)
        self.remove_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.add_btn)
        buttons_layout.addWidget(self.remove_btn)
        
        layout.addLayout(buttons_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_editor_panel(self) -> QGroupBox:
        """Создание панели редактирования категории"""
        group = QGroupBox("Настройки категории")
        layout = QVBoxLayout()
        
        # Название категории
        name_layout = QHBoxLayout()
        name_label = QLabel("Название:")
        name_label.setMinimumWidth(100)
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self.on_settings_changed)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # Приоритет
        priority_layout = QHBoxLayout()
        priority_label = QLabel("Приоритет:")
        priority_label.setMinimumWidth(100)
        self.priority_spin = QSpinBox()
        self.priority_spin.setMinimum(1)
        self.priority_spin.setMaximum(999)
        self.priority_spin.setToolTip("Чем меньше число, тем выше приоритет проверки")
        self.priority_spin.valueChanged.connect(self.on_settings_changed)
        priority_layout.addWidget(priority_label)
        priority_layout.addWidget(self.priority_spin)
        priority_layout.addStretch()
        layout.addLayout(priority_layout)
        
        # Включена/выключена
        self.enabled_check = QCheckBox("Категория включена")
        self.enabled_check.setChecked(True)
        self.enabled_check.stateChanged.connect(self.on_settings_changed)
        layout.addWidget(self.enabled_check)
        
        # Разделитель
        layout.addWidget(QLabel(""))
        
        # Правила по базе данных имен
        name_db_group = self._create_name_database_group()
        layout.addWidget(name_db_group)
        
        # Правила по контроллеру
        controller_group = self._create_controller_group()
        layout.addWidget(controller_group)
        
        # Правила по расширениям
        extensions_group = self._create_extensions_group()
        layout.addWidget(extensions_group)
        
        layout.addStretch()
        
        # Кнопки сохранения
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_all)
        self.save_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_name_database_group(self) -> QGroupBox:
        """Создание группы настроек базы данных имен"""
        group = QGroupBox("База данных имен")
        layout = QVBoxLayout()
        
        # Чекбокс включения
        self.name_db_enabled = QCheckBox("Использовать базу данных имен")
        self.name_db_enabled.stateChanged.connect(self.on_settings_changed)
        self.name_db_enabled.stateChanged.connect(self.toggle_name_db_controls)
        layout.addWidget(self.name_db_enabled)
        
        # Алгоритм сравнения
        algo_layout = QHBoxLayout()
        algo_label = QLabel("Алгоритм:")
        self.name_db_algorithm = QComboBox()
        self.name_db_algorithm.addItems([
            "exact - Точное совпадение",
            "partial - Частичное совпадение",
            "case_insensitive - Без учета регистра"
        ])
        self.name_db_algorithm.currentIndexChanged.connect(self.on_settings_changed)
        algo_layout.addWidget(algo_label)
        algo_layout.addWidget(self.name_db_algorithm)
        layout.addLayout(algo_layout)
        
        # Список имен
        items_label = QLabel("Список имен (по одному на строку):")
        layout.addWidget(items_label)
        
        self.name_db_items = QTextEdit()
        self.name_db_items.setMaximumHeight(100)
        self.name_db_items.textChanged.connect(self.on_settings_changed)
        layout.addWidget(self.name_db_items)
        
        group.setLayout(layout)
        return group
    
    def _create_controller_group(self) -> QGroupBox:
        """Создание группы настроек контроллера"""
        group = QGroupBox("Контроллер лаунчера")
        layout = QVBoxLayout()
        
        # Чекбокс включения
        self.controller_enabled = QCheckBox("Использовать контроллер")
        self.controller_enabled.stateChanged.connect(self.on_settings_changed)
        self.controller_enabled.stateChanged.connect(self.toggle_controller_controls)
        layout.addWidget(self.controller_enabled)
        
        # Выбор типа контроллера
        type_layout = QHBoxLayout()
        type_label = QLabel("Тип:")
        self.controller_type = QComboBox()
        self.controller_type.addItems(["steam", "epic", "gog"])  # Пока только steam реализован
        self.controller_type.currentIndexChanged.connect(self.on_settings_changed)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.controller_type)
        layout.addLayout(type_layout)
        
        # Кнопка сканирования
        self.scan_btn = QPushButton("Сканировать директорию")
        self.scan_btn.clicked.connect(self.scan_controller_directory)
        layout.addWidget(self.scan_btn)
        
        # Дополнительные настройки
        self.controller_check_appid = QCheckBox("Проверять AppID (для Steam)")
        self.controller_check_appid.setChecked(True)
        self.controller_check_appid.stateChanged.connect(self.on_settings_changed)
        layout.addWidget(self.controller_check_appid)
        
        group.setLayout(layout)
        return group
    
    def _create_extensions_group(self) -> QGroupBox:
        """Создание группы настроек расширений"""
        group = QGroupBox("Расширения файлов")
        layout = QVBoxLayout()
        
        # Чекбокс включения
        self.extensions_enabled = QCheckBox("Использовать расширения")
        self.extensions_enabled.stateChanged.connect(self.on_settings_changed)
        self.extensions_enabled.stateChanged.connect(self.toggle_extensions_controls)
        layout.addWidget(self.extensions_enabled)
        
        # Список расширений
        ext_label = QLabel("Расширения (через запятую, с точкой):")
        layout.addWidget(ext_label)
        
        self.extensions_edit = QLineEdit()
        self.extensions_edit.setPlaceholderText("Например: .jpg, .png, .gif")
        self.extensions_edit.textChanged.connect(self.on_settings_changed)
        layout.addWidget(self.extensions_edit)
        
        group.setLayout(layout)
        return group
    
    def load_categories(self) -> None:
        """Загрузка списка категорий"""
        self.category_list.clear()
        
        for category in self.categories:
            item = QListWidgetItem(str(category.get("name", "")))
            if not category.get("enabled", True):
                item.setForeground(Qt.GlobalColor.gray)
            self.category_list.addItem(item)
        
        if len(self.categories) > 0:
            self.category_list.setCurrentRow(0)
    
    def on_category_selected(self, index: int) -> None:
        """Обработка выбора категории из списка"""
        if index < 0 or index >= len(self.categories):
            self.current_index = -1
            self.remove_btn.setEnabled(False)
            self.clear_editor()
            return
        
        self.current_index = index
        self.remove_btn.setEnabled(True)
        self.load_category_to_editor(self.categories[index])
    
    def load_category_to_editor(self, category: CategoryDict) -> None:
        """Загрузка данных категории в редактор"""
        # Блокируем сигналы для предотвращения ложных изменений
        self.block_signals(True)
        
        # Основные настройки
        self.name_edit.setText(category.get("name", ""))
        self.priority_spin.setValue(category.get("priority", 999))
        self.enabled_check.setChecked(category.get("enabled", True))
        
        rules = category.get("rules", {})
        
        # База данных имен
        name_db = rules.get("name_database")
        if name_db:
            self.name_db_enabled.setChecked(name_db.get("enabled", False))
            
            algorithm = name_db.get("algorithm", "exact")
            algo_map = {"exact": 0, "partial": 1, "case_insensitive": 2}
            self.name_db_algorithm.setCurrentIndex(algo_map.get(algorithm, 0))
            
            items = name_db.get("items", [])
            self.name_db_items.setPlainText("\n".join(items))
        
        # Контроллер
        controller = rules.get("controller")
        if controller:
            self.controller_enabled.setChecked(controller.get("enabled", False))
            
            ctrl_type = controller.get("type", "steam")
            type_map = {"steam": 0, "epic": 1, "gog": 2}
            self.controller_type.setCurrentIndex(type_map.get(ctrl_type, 0))
            
            config = controller.get("config")
            if config:
                self.controller_check_appid.setChecked(config.get("check_appid", True))
        
        # Расширения
        extensions = rules.get("extensions")
        if extensions:
            self.extensions_enabled.setChecked(extensions.get("enabled", False))
            
            ext_list = extensions.get("list", [])
            self.extensions_edit.setText(", ".join(ext_list))
        
        # Разблокируем сигналы
        self.block_signals(False)
        
        # Обновляем состояние контролов
        self.toggle_name_db_controls()
        self.toggle_controller_controls()
        self.toggle_extensions_controls()
    
    def save_current_category(self) -> None:
        """Сохранение текущей редактируемой категории"""
        if self.current_index < 0 or self.current_index >= len(self.categories):
            return
        
        # Парсинг алгоритма
        algo_text = self.name_db_algorithm.currentText()
        algorithm = algo_text.split(" - ")[0] if " - " in algo_text else "exact"
        
        # Парсинг элементов базы данных
        name_db_items_text = self.name_db_items.toPlainText()
        name_db_items_list = [item.strip() for item in name_db_items_text.split("\n") if item.strip()]
        
        # Парсинг расширений
        extensions_text = self.extensions_edit.text()
        extensions_list = [ext.strip() for ext in extensions_text.split(",") if ext.strip()]
        
        # Парсинг типа контроллера
        ctrl_type_text = self.controller_type.currentText()
        ctrl_type = ctrl_type_text if ctrl_type_text in ["steam", "epic", "gog"] else "steam"
        
        # Обновление категории
        category: CategoryDict = {
            "name": self.name_edit.text(),
            "enabled": self.enabled_check.isChecked(),
            "priority": self.priority_spin.value(),
            "rules": {
                "name_database": {
                    "enabled": self.name_db_enabled.isChecked(),
                    "algorithm": algorithm,
                    "items": name_db_items_list
                },
                "controller": {
                    "enabled": self.controller_enabled.isChecked(),
                    "type": ctrl_type,
                    "config": {
                        "check_appid": self.controller_check_appid.isChecked()
                    }
                },
                "extensions": {
                    "enabled": self.extensions_enabled.isChecked(),
                    "list": extensions_list
                }
            }
        }
        
        self.categories[self.current_index] = category
        
        # Обновление списка
        item = self.category_list.item(self.current_index)
        if item:
            item.setText(self.name_edit.text())
            if not self.enabled_check.isChecked():
                item.setForeground(Qt.GlobalColor.gray)
            else:
                item.setForeground(Qt.GlobalColor.black)
    def clear_editor(self) -> None:
        """Очистка редактора"""
        self.block_signals(True)
        
        self.name_edit.clear()
        self.priority_spin.setValue(999)
        self.enabled_check.setChecked(True)
        
        self.name_db_enabled.setChecked(False)
        self.name_db_algorithm.setCurrentIndex(0)
        self.name_db_items.clear()
        
        self.controller_enabled.setChecked(False)
        self.controller_type.setCurrentIndex(0)
        self.controller_check_appid.setChecked(True)
        
        self.extensions_enabled.setChecked(False)
        self.extensions_edit.clear()
        
        self.block_signals(False)
    
    def block_signals(self, block: bool) -> None:
        """Блокировка/разблокировка сигналов всех контролов"""
        widgets = [
            self.name_edit, self.priority_spin, self.enabled_check,
            self.name_db_enabled, self.name_db_algorithm, self.name_db_items,
            self.controller_enabled, self.controller_type, self.controller_check_appid,
            self.extensions_enabled, self.extensions_edit
        ]
        
        for widget in widgets:
            widget.blockSignals(block)
    
    def on_settings_changed(self) -> None:
        """Обработка изменения настроек"""
        self.save_btn.setEnabled(True)
    
    def toggle_name_db_controls(self) -> None:
        """Включение/выключение контролов базы данных имен"""
        enabled = self.name_db_enabled.isChecked()
        self.name_db_algorithm.setEnabled(enabled)
        self.name_db_items.setEnabled(enabled)
    
    def toggle_controller_controls(self) -> None:
        """Включение/выключение контролов контроллера"""
        enabled = self.controller_enabled.isChecked()
        self.controller_type.setEnabled(enabled)
        self.scan_btn.setEnabled(enabled)
        self.controller_check_appid.setEnabled(enabled)
    
    def toggle_extensions_controls(self) -> None:
        """Включение/выключение контролов расширений"""
        enabled = self.extensions_enabled.isChecked()
        self.extensions_edit.setEnabled(enabled)
    
    def scan_controller_directory(self) -> None:
        """Сканирование директории контроллером"""
        ctrl_type = self.controller_type.currentText()
        
        if ctrl_type != "steam":
            QMessageBox.information(
                self,
                "Информация",
                f"Контроллер {ctrl_type} еще не реализован.\nПока доступен только Steam."
            )
            return
        
        # Выбор директории
        directory = QFileDialog.getExistingDirectory(
            self,
            "Выберите директорию Steam (steamapps/common/)",
            ""
        )
        
        if not directory:
            return
        
        # Сканирование
        controller = SteamController()
        items = controller.scan_directory(directory)
        
        if not items:
            QMessageBox.warning(
                self,
                "Предупреждение",
                "Не найдено ни одной игры в указанной директории."
            )
            return
        
        # Добавление найденных элементов в базу данных
        current_items = self.name_db_items.toPlainText().split("\n")
        current_items = [item.strip() for item in current_items if item.strip()]
        
        new_items = set(current_items + items)
        self.name_db_items.setPlainText("\n".join(sorted(new_items)))
        
        # Включаем базу данных имен если она была выключена
        if not self.name_db_enabled.isChecked():
            self.name_db_enabled.setChecked(True)
        
        QMessageBox.information(
            self,
            "Успешно",
            f"Добавлено игр: {len(items)}\n\nНе забудьте сохранить изменения!"
        )
    
    def add_category(self) -> None:
        """Добавление новой категории"""
        new_category: CategoryDict = {
            "name": "Новая категория",
            "enabled": True,
            "priority": len(self.categories) + 1,
            "rules": {
                "name_database": {
                    "enabled": False,
                    "algorithm": "exact",
                    "items": []
                },
                "controller": {
                    "enabled": False,
                    "type": "steam",
                    "config": {
                        "check_appid": True
                    }
                },
                "extensions": {
                    "enabled": True,
                    "list": []
                }
            }
        }
        
        self.categories.append(new_category)
        
        item = QListWidgetItem("Новая категория")
        self.category_list.addItem(item)
        self.category_list.setCurrentRow(len(self.categories) - 1)
        
        self.save_btn.setEnabled(True)
    
    def remove_category(self) -> None:
        """Удаление выбранной категории"""
        if self.current_index < 0:
            return
        
        category_name = self.categories[self.current_index].get("name", "")
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить категорию '{category_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Удаление
        del self.categories[self.current_index]
        self.category_list.takeItem(self.current_index)
        
        self.save_btn.setEnabled(True)
    
    def save_all(self) -> None:
        """Сохранение всех изменений"""
        # Сохраняем текущую категорию
        if self.current_index >= 0:
            self.save_current_category()
        
        # Сохраняем в конфиг
        self.config_manager.update_categories(self.categories)
        
        QMessageBox.information(
            self,
            "Успешно",
            "Настройки категорий сохранены!"
        )
        
        self.save_btn.setEnabled(False)
        self.accept()