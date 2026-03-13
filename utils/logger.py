import logging
import os
from datetime import datetime
from pathlib import Path

def setup_logger():
    """Настройка логирования в файл и консоль"""
    # Создание папки для логов
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Имя файла с текущей датой
    log_filename = log_dir / f"sorter_{datetime.now().strftime('%Y-%m-%d')}.log"
    
    # Настройка формата
    log_format = '[%(asctime)s] [%(levelname)s] %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Базовая настройка
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def get_logger():
    """Получить логгер"""
    return logging.getLogger(__name__)
