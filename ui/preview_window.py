from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTreeWidget, QTreeWidgetItem, QLabel, QSplitter,
    QHeaderView, QWidget, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QDrag
from typing import List, Dict, Optional
from pathlib import Path
from collections import defaultdict

from core.sorter import SortResult

class PreviewWindow(QDialog):
    """Окно предпросмотра сортировки с возможностью редактирования"""
    
    # Сигнал для передачи измененных результатов
    results_confirmed = Signal(list)  # Signal[List[SortResult]]
    
    def __init__(
        self,
        results: List[SortResult],
        source_dir: Path,
        target_dir: Path,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.results = results
        self.source_dir = source_dir
        self.target_dir = target_dir
        
        # Словарь для отслеживания изменений категорий
        self.result_map: Dict[str, SortResult] = {
            str(r.source): r for r in results
        }
        
        self.init_ui()
        self.populate_trees()
    
    def init_ui(self) -> None:
        """Инициализация интерфейса"""
        self.setWindowTitle("Предпросмотр сортировки")
        self.setMinimumSize(1200, 700)
        
        layout = QVBoxLayout(self)
        
        # Заголовок
        header_label = QLabel(
            f"<b>Будет обработано файлов: {len(self.results)}</b><br><br>"
            "Слева — текущая структура, справа — после сортировки<br>"
            "<i>Перетаскивайте файлы между категориями справа для изменения</i>"
        )
        header_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        layout.addWidget(header_label)
        
        # Разделитель с двумя деревьями
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Левое дерево - текущая структура (только просмотр)
        self.before_tree = self._create_tree("📁 Текущая структура", enable_drag=False)
        splitter.addWidget(self.before_tree)
        
        # Правое дерево - после сортировки (с drag-and-drop)
        self.after_tree = self._create_tree("📂 После сортировки (редактируется)", enable_drag=True)
        splitter.addWidget(self.after_tree)
        
        splitter.setSizes([600, 600])
        layout.addWidget(splitter)
        
        # Легенда
        legend_layout = QHBoxLayout()
        
        legend_label = QLabel("Легенда:")
        legend_label.setStyleSheet("font-weight: bold;")
        legend_layout.addWidget(legend_label)
        
        normal_label = QLabel("⚫ Будет перемещен")
        legend_layout.addWidget(normal_label)
        
        duplicate_label = QLabel("🟠 Дубликат")
        duplicate_label.setStyleSheet("color: orange;")
        legend_layout.addWidget(duplicate_label)
        
        modified_label = QLabel("🔵 Изменено пользователем")
        modified_label.setStyleSheet("color: blue;")
        legend_layout.addWidget(modified_label)
        
        legend_layout.addStretch()
        layout.addLayout(legend_layout)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("↺ Сбросить изменения")
        self.reset_btn.clicked.connect(self.reset_changes)
        self.reset_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("✖ Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.apply_btn = QPushButton("✔ Применить и сортировать")
        self.apply_btn.clicked.connect(self.confirm_and_sort)
        self.apply_btn.setStyleSheet("font-weight: bold; padding: 8px 16px;")
        
        buttons_layout.addWidget(self.reset_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.apply_btn)
        
        layout.addLayout(buttons_layout)
    
    def _create_tree(self, title: str, enable_drag: bool = False) -> QTreeWidget:
        """Создание дерева файлов"""
        tree = QTreeWidget()
        tree.setHeaderLabels([title, "Тип", "Правило"])
        tree.setColumnWidth(0, 400)
        tree.setColumnWidth(1, 80)
        tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        tree.setAlternatingRowColors(True)
        
        if enable_drag:
            tree.setDragEnabled(True)
            tree.setAcceptDrops(True)
            tree.setDropIndicatorShown(True)
            tree.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
            # Переопределяем обработчики drag-and-drop
            tree.dragEnterEvent = lambda e: self._drag_enter_event(e, tree)
            tree.dragMoveEvent = lambda e: self._drag_move_event(e, tree)
            tree.dropEvent = lambda e: self._drop_event(e, tree)
        else:
            tree.setDragDropMode(QTreeWidget.DragDropMode.NoDragDrop)
        
        return tree
    
    def populate_trees(self) -> None:
        """Заполнение деревьев данными"""
        # Группировка результатов
        before_structure: Dict[str, List[SortResult]] = defaultdict(list)
        after_structure: Dict[str, List[SortResult]] = defaultdict(list)
        
        for result in self.results:
            # Текущая структура
            if result.source.is_file():
                parent_name = result.source.parent.name if result.source.parent != self.source_dir else "📁 Корень"
            else:
                parent_name = "📁 Корень"
            
            before_structure[parent_name].append(result)
            
            # Будущая структура
            after_structure[result.category].append(result)
        
        # Заполнение левого дерева (текущая структура - только файлы)
        for folder_name in sorted(before_structure.keys()):
            folder_item = QTreeWidgetItem(self.before_tree, [folder_name, "Папка", ""])
            folder_item.setExpanded(True)
            
            for result in sorted(before_structure[folder_name], key=lambda x: x.source.name):
                if result.source.is_file():  # Показываем только файлы
                    file_item = QTreeWidgetItem(folder_item, [
                        result.source.name,
                        "Файл",
                        result.rule_type
                    ])
                    self._apply_color(file_item, result)
        
        # Заполнение правого дерева (после сортировки - файлы по категориям)
        self._populate_after_tree()
    
    def _populate_after_tree(self) -> None:
        """Заполнение правого дерева с категориями"""
        self.after_tree.clear()
        
        # Группировка по категориям
        after_structure: Dict[str, List[SortResult]] = defaultdict(list)
        for result in self.results:
            after_structure[result.category].append(result)
        
        # Создание категорий с файлами
        for category_name in sorted(after_structure.keys()):
            category_item = QTreeWidgetItem(self.after_tree, [
                f"📂 {category_name}",
                "Категория",
                ""
            ])
            category_item.setExpanded(True)
            category_item.setData(0, Qt.ItemDataRole.UserRole, category_name)  # Сохраняем имя категории
            
            # Добавляем файлы в категорию
            for result in sorted(after_structure[category_name], key=lambda x: x.source.name):
                file_item = QTreeWidgetItem(category_item, [
                    result.source.name,
                    "Файл",
                    result.rule_type
                ])
                # Сохраняем путь к файлу для идентификации
                file_item.setData(0, Qt.ItemDataRole.UserRole, str(result.source))
                
                self._apply_color(file_item, result)
    
    def _apply_color(self, item: QTreeWidgetItem, result: SortResult) -> None:
        """Применение цвета к элементу дерева"""
        if result.category == "Дубликаты":
            item.setForeground(0, QColor("orange"))
        elif hasattr(result, 'modified') and result.modified:  # type: ignore
            item.setForeground(0, QColor("blue"))
        elif not result.success and result.category != "Пропущено":
            item.setForeground(0, QColor("red"))
    
    def _drag_enter_event(self, event: 'QDragEnterEvent', tree: QTreeWidget) -> None:  # type: ignore
        """Обработка начала перетаскивания"""
        if event.source() == tree:
            event.accept()
        else:
            event.ignore()
    
    def _drag_move_event(self, event: 'QDragMoveEvent', tree: QTreeWidget) -> None:  # type: ignore
        """Обработка движения при перетаскивании"""
        if event.source() == tree:
            event.accept()
        else:
            event.ignore()
    
    def _drop_event(self, event: 'QDropEvent', tree: QTreeWidget) -> None:  # type: ignore
        """Обработка отпускания при перетаскивании"""
        source_item = tree.currentItem()
        target_item = tree.itemAt(event.position().toPoint())
        
        if not source_item or not target_item:
            event.ignore()
            return
        
        # Получаем путь к файлу
        file_path = source_item.data(0, Qt.ItemDataRole.UserRole)
        if not file_path or not isinstance(file_path, str):
            event.ignore()
            return
        
        # Определяем целевую категорию
        target_category = None
        
        # Если бросили на категорию
        if target_item.parent() is None:
            target_category = target_item.data(0, Qt.ItemDataRole.UserRole)
        # Если бросили на файл внутри категории
        elif target_item.parent() is not None:
            target_category = target_item.parent().data(0, Qt.ItemDataRole.UserRole)
        
        if not target_category or not isinstance(target_category, str):
            event.ignore()
            return
        
        # Обновляем категорию в результате
        if file_path in self.result_map:
            old_category = self.result_map[file_path].category
            if old_category != target_category:
                self.result_map[file_path].category = target_category
                self.result_map[file_path].modified = True  # type: ignore
                
                # Перерисовываем дерево
                self._populate_after_tree()
                self.reset_btn.setEnabled(True)
        
        event.accept()
    
    def reset_changes(self) -> None:
        """Сброс всех изменений пользователя"""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Сбросить все внесенные изменения?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Восстанавливаем исходные категории
            for result in self.results:
                if hasattr(result, 'modified'):
                    delattr(result, 'modified')
            
            self._populate_after_tree()
            self.reset_btn.setEnabled(False)
    
    def confirm_and_sort(self) -> None:
        """Подтверждение и отправка результатов для сортировки"""
        modified_count = sum(1 for r in self.results if hasattr(r, 'modified') and r.modified)  # type: ignore
        
        message = f"Начать сортировку {len(self.results)} файлов?"
        if modified_count > 0:
            message += f"\n\nВы изменили категорию для {modified_count} файлов."
        
        reply = QMessageBox.question(
            self,
            "Подтверждение сортировки",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.results_confirmed.emit(list(self.result_map.values()))
            self.accept()
