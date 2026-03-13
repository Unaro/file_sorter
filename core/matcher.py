from enum import Enum
from pathlib import Path
from typing import List, Optional

class MatchAlgorithm(Enum):
    """Алгоритмы сопоставления имен"""
    EXACT = "exact"
    PARTIAL = "partial"
    CASE_INSENSITIVE = "case_insensitive"

class Matcher:
    """Класс для сопоставления файлов с категориями"""
    
    @staticmethod
    def match_by_name(filename: str, database: List[str], algorithm: str) -> bool:
        """
        Проверка совпадения имени файла с базой данных
        
        Args:
            filename: Имя файла
            database: Список имен в базе данных
            algorithm: Алгоритм сравнения
        
        Returns:
            True если найдено совпадение
        """
        if not database:
            return False
        
        # Убираем расширение из имени файла
        file_stem = Path(filename).stem
        
        for db_name in database:
            if algorithm == MatchAlgorithm.EXACT.value:
                if file_stem == db_name:
                    return True
            
            elif algorithm == MatchAlgorithm.PARTIAL.value:
                if db_name.lower() in file_stem.lower():
                    return True
            
            elif algorithm == MatchAlgorithm.CASE_INSENSITIVE.value:
                if file_stem.lower() == db_name.lower():
                    return True
        
        return False
    
    @staticmethod
    def match_by_extension(filename: str, extensions: List[str]) -> bool:
        """
        Проверка совпадения расширения файла
        
        Args:
            filename: Имя файла
            extensions: Список расширений
        
        Returns:
            True если расширение подходит
        """
        if not extensions:
            return False
        
        file_ext = Path(filename).suffix.lower()
        return file_ext in [ext.lower() for ext in extensions]
