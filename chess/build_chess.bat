@echo off
chcp 65001 >nul
echo ========================================
echo Сборка шахмат в .exe файл
echo ========================================
echo.

echo Шаг 1: Установка зависимостей...
pip install -r requirements.txt

echo.
echo Шаг 2: Загрузка ресурсов (опционально)...
python download_resources.py

echo.
echo Шаг 3: Сборка .exe файла...
pyinstaller --onefile --windowed --name=Шахматы --add-data "pieces;pieces" --add-data "sounds;sounds" chess_game.py

echo.
echo ========================================
echo Готово!
echo ========================================
echo Файл находится в папке dist: Шахматы.exe
echo.
pause

