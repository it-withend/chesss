"""
Утилита для загрузки изображений фигур и звуков из интернета
"""
import os
import urllib.request
import json

# Маппинг имен файлов для разных источников
PIECE_FILENAMES = {
    'white_king': 'wk',
    'white_queen': 'wq',
    'white_rook': 'wr',
    'white_bishop': 'wb',
    'white_knight': 'wn',
    'white_pawn': 'wp',
    'black_king': 'bk',
    'black_queen': 'bq',
    'black_rook': 'br',
    'black_bishop': 'bb',
    'black_knight': 'bn',
    'black_pawn': 'bp',
}

# Источники изображений (пробуем по порядку)
IMAGE_SOURCES = [
    # Lichess (открытый источник)
    {
        'base_url': 'https://raw.githubusercontent.com/lichess-org/lila/master/public/piece/cburnett/',
        'extension': '.png',
        'format': '{filename}.png'
    },
    # Chess.com CDN (может не работать без правильных заголовков)
    {
        'base_url': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/',
        'extension': '.png',
        'format': '{filename}.png'
    },
    # Альтернативный источник
    {
        'base_url': 'https://www.chess.com/chess-themes/pieces/neo/150/',
        'extension': '.png',
        'format': '{filename}.png'
    },
]

def download_file(url: str, filepath: str) -> bool:
    """Загрузить файл по URL"""
    try:
        print(f"Загрузка {url}...")
        urllib.request.urlretrieve(url, filepath)
        print(f"✓ Успешно загружено: {filepath}")
        return True
    except Exception as e:
        print(f"✗ Ошибка загрузки {url}: {e}")
        return False

def create_directories():
    """Создать необходимые директории"""
    directories = ['pieces', 'sounds']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Создана директория: {directory}")

def download_piece_images():
    """Загрузить изображения фигур"""
    print("\n=== Загрузка изображений фигур ===")
    create_directories()
    
    downloaded = 0
    total = len(PIECE_FILENAMES)
    
    for key, filename in PIECE_FILENAMES.items():
        filepath = f"pieces/{key}.png"
        
        # Пропускаем если уже существует
        if os.path.exists(filepath):
            print(f"⊘ Пропущено (уже существует): {filepath}")
            continue
        
        # Пробуем загрузить из разных источников
        success = False
        for source in IMAGE_SOURCES:
            url = source['base_url'] + source['format'].format(filename=filename)
            if download_file(url, filepath):
                success = True
                downloaded += 1
                break
        
        if not success:
            print(f"⚠ Не удалось загрузить: {key} (будет использован Unicode символ)")
    
    print(f"\n✓ Загружено изображений: {downloaded}/{total}")
    if downloaded < total:
        print("  Игра будет использовать Unicode символы для недостающих фигур")

def download_sounds():
    """Загрузить звуковые эффекты"""
    print("\n=== Загрузка звуковых эффектов ===")
    create_directories()
    
    # Примеры URL для звуков (замените на реальные)
    sound_urls = {
        'move': 'https://www.soundjay.com/misc/sounds/bell-ringing-05.wav',
        'capture': 'https://www.soundjay.com/misc/sounds/click-09.wav',
        'check': 'https://www.soundjay.com/misc/sounds/alert-09.wav',
        'checkmate': 'https://www.soundjay.com/misc/sounds/fail-buzzer-02.wav',
    }
    
    print("⚠ Звуки требуют ручной загрузки или использования библиотек")
    print("Рекомендуется использовать бесплатные звуки с:")
    print("  - freesound.org")
    print("  - zapsplat.com")
    print("  - mixkit.co")
    
    # Создаем заглушки
    for sound_name in ['move', 'capture', 'check', 'checkmate']:
        filepath = f"sounds/{sound_name}.wav"
        if not os.path.exists(filepath):
            print(f"⚠ Создайте файл: {filepath}")

def generate_fallback_images():
    """Создать простые изображения-заглушки если загрузка не удалась"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        print("\n=== Создание заглушек для изображений ===")
        create_directories()
        
        piece_colors = {
            'white': (255, 255, 255),
            'black': (0, 0, 0),
        }
        
        piece_symbols = {
            'king': '♔♚',
            'queen': '♕♛',
            'rook': '♖♜',
            'bishop': '♗♝',
            'knight': '♘♞',
            'pawn': '♙♟',
        }
        
        for color in ['white', 'black']:
            bg_color = (200, 200, 200) if color == 'white' else (100, 100, 100)
            text_color = (0, 0, 0) if color == 'white' else (255, 255, 255)
            
            for piece_type in piece_symbols.keys():
                key = f"{color}_{piece_type}"
                filepath = f"pieces/{key}.png"
                
                if os.path.exists(filepath):
                    continue
                
                img = Image.new('RGB', (150, 150), bg_color)
                draw = ImageDraw.Draw(img)
                
                # Пытаемся использовать шрифт
                try:
                    font = ImageFont.truetype("arial.ttf", 100)
                except:
                    font = ImageFont.load_default()
                
                symbol_index = 0 if color == 'white' else 1
                symbol = piece_symbols[piece_type][symbol_index]
                
                # Центрируем текст
                bbox = draw.textbbox((0, 0), symbol, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                position = ((150 - text_width) // 2, (150 - text_height) // 2)
                
                draw.text(position, symbol, fill=text_color, font=font)
                img.save(filepath)
                print(f"✓ Создана заглушка: {filepath}")
        
        print("✓ Заглушки созданы успешно")
    except ImportError:
        print("⚠ PIL не установлен, пропускаем создание заглушек")
        print("  Установите: pip install Pillow")

def main():
    """Главная функция"""
    print("=" * 50)
    print("Загрузка ресурсов для шахмат")
    print("=" * 50)
    
    download_piece_images()
    download_sounds()
    
    # Пытаемся создать заглушки
    try:
        generate_fallback_images()
    except Exception as e:
        print(f"⚠ Ошибка при создании заглушек: {e}")
    
    print("\n" + "=" * 50)
    print("Загрузка завершена!")
    print("=" * 50)
    print("\nПримечание:")
    print("- Если изображения не загрузились, игра будет использовать Unicode символы")
    print("- Звуки можно добавить вручную в папку 'sounds/'")
    print("- Игра полностью функциональна даже без загруженных ресурсов")

if __name__ == "__main__":
    main()

