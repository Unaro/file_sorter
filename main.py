import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from utils.logger import setup_logger

def main():
    # Настройка логирования
    setup_logger()
    
    # Создание приложения
    app = QApplication(sys.argv)
    app.setApplicationName("Сортировщик файлов")
    app.setOrganizationName("FileSorter")
    
    # Создание главного окна
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
