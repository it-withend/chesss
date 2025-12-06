import pygame
import sys
import json
import os
import urllib.request
from typing import List, Tuple, Optional
import time
import random

# Инициализация Pygame
pygame.init()
pygame.mixer.init()

# Константы
BOARD_SIZE = 8
SQUARE_SIZE = 80
BOARD_WIDTH = BOARD_SIZE * SQUARE_SIZE
BOARD_HEIGHT = BOARD_SIZE * SQUARE_SIZE
PANEL_WIDTH = 300
WINDOW_WIDTH = BOARD_WIDTH + PANEL_WIDTH
WINDOW_HEIGHT = BOARD_HEIGHT + 100

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT = (255, 255, 0, 128)
MOVE_HIGHLIGHT = (0, 255, 0, 100)
ATTACK_HIGHLIGHT = (255, 0, 0, 100)
SELECTED_HIGHLIGHT = (255, 215, 0, 150)
CHECK_HIGHLIGHT = (255, 0, 0, 200)
GOLD = (255, 215, 0)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (200, 200, 200)

class Piece:
    def __init__(self, color: str, piece_type: str):
        self.color = color  # 'white' or 'black'
        self.type = piece_type  # 'pawn', 'rook', 'knight', 'bishop', 'queen', 'king'
        self.has_moved = False
        self.image = None
        
    def get_symbol(self) -> str:
        """Возвращает Unicode символ фигуры"""
        symbols = {
            'white': {'king': '♔', 'queen': '♕', 'rook': '♖', 'bishop': '♗', 'knight': '♘', 'pawn': '♙'},
            'black': {'king': '♚', 'queen': '♛', 'rook': '♜', 'bishop': '♝', 'knight': '♞', 'pawn': '♟'}
        }
        return symbols[self.color][self.type]

class ChessBoard:
    def __init__(self):
        self.board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.setup_board()
        self.current_turn = 'white'
        self.move_history = []
        self.white_king_pos = (7, 4)
        self.black_king_pos = (0, 4)
        self.in_check = {'white': False, 'black': False}
        self.game_over = False
        self.winner = None
        
    def setup_board(self):
        """Начальная расстановка фигур"""
        # Пешки
        for col in range(BOARD_SIZE):
            self.board[1][col] = Piece('black', 'pawn')
            self.board[6][col] = Piece('white', 'pawn')
        
        # Ладьи
        self.board[0][0] = Piece('black', 'rook')
        self.board[0][7] = Piece('black', 'rook')
        self.board[7][0] = Piece('white', 'rook')
        self.board[7][7] = Piece('white', 'rook')
        
        # Кони
        self.board[0][1] = Piece('black', 'knight')
        self.board[0][6] = Piece('black', 'knight')
        self.board[7][1] = Piece('white', 'knight')
        self.board[7][6] = Piece('white', 'knight')
        
        # Слоны
        self.board[0][2] = Piece('black', 'bishop')
        self.board[0][5] = Piece('black', 'bishop')
        self.board[7][2] = Piece('white', 'bishop')
        self.board[7][5] = Piece('white', 'bishop')
        
        # Ферзи
        self.board[0][3] = Piece('black', 'queen')
        self.board[7][3] = Piece('white', 'queen')
        
        # Короли
        self.board[0][4] = Piece('black', 'king')
        self.board[7][4] = Piece('white', 'king')
    
    def get_piece(self, row: int, col: int) -> Optional[Piece]:
        """Получить фигуру на позиции"""
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            return self.board[row][col]
        return None
    
    def is_valid_move(self, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        """Проверка валидности хода"""
        start_row, start_col = start
        end_row, end_col = end
        
        piece = self.get_piece(start_row, start_col)
        if not piece or piece.color != self.current_turn:
            return False
        
        target = self.get_piece(end_row, end_col)
        if target and target.color == piece.color:
            return False
        
        # Король не может быть взят!
        if target and target.type == 'king':
            return False
        
        # Проверка правил движения фигур
        if not self.is_valid_piece_move(piece, start, end):
            return False
        
        # Проверка на шах после хода
        if self.would_be_in_check(start, end):
            return False
        
        return True
    
    def is_valid_piece_move(self, piece: Piece, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        """Проверка правил движения конкретной фигуры"""
        start_row, start_col = start
        end_row, end_col = end
        row_diff = end_row - start_row
        col_diff = end_col - start_col
        
        if piece.type == 'pawn':
            direction = -1 if piece.color == 'white' else 1
            start_row_pawn = 6 if piece.color == 'white' else 1
            
            # Движение вперед
            if col_diff == 0:
                if end_row == start_row + direction:
                    return self.get_piece(end_row, end_col) is None
                elif end_row == start_row + 2 * direction and start_row == start_row_pawn:
                    return (self.get_piece(end_row, end_col) is None and 
                           self.get_piece(start_row + direction, start_col) is None)
            # Взятие
            elif abs(col_diff) == 1 and end_row == start_row + direction:
                return self.get_piece(end_row, end_col) is not None
        
        elif piece.type == 'rook':
            if row_diff == 0 or col_diff == 0:
                return self.is_path_clear(start, end)
        
        elif piece.type == 'bishop':
            if abs(row_diff) == abs(col_diff):
                return self.is_path_clear(start, end)
        
        elif piece.type == 'queen':
            if (row_diff == 0 or col_diff == 0 or abs(row_diff) == abs(col_diff)):
                return self.is_path_clear(start, end)
        
        elif piece.type == 'king':
            if abs(row_diff) <= 1 and abs(col_diff) <= 1:
                return True
            # Рокировка
            if not piece.has_moved and col_diff == 0:
                if abs(row_diff) == 2:
                    return self.can_castle(start, end)
        
        elif piece.type == 'knight':
            return (abs(row_diff) == 2 and abs(col_diff) == 1) or (abs(row_diff) == 1 and abs(col_diff) == 2)
        
        return False
    
    def is_path_clear(self, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        """Проверка, свободен ли путь"""
        start_row, start_col = start
        end_row, end_col = end
        
        row_step = 1 if end_row > start_row else -1 if end_row < start_row else 0
        col_step = 1 if end_col > start_col else -1 if end_col < start_col else 0
        
        row, col = start_row + row_step, start_col + col_step
        while (row, col) != (end_row, end_col):
            if self.get_piece(row, col) is not None:
                return False
            row += row_step
            col += col_step
        
        return True
    
    def can_castle(self, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        """Проверка возможности рокировки"""
        start_row, start_col = start
        end_row, end_col = end
        
        if start_col != 4:  # Король должен быть на начальной позиции
            return False
        
        # Определяем сторону рокировки
        if end_col == 6:  # Короткая рокировка
            rook_col = 7
        elif end_col == 2:  # Длинная рокировка
            rook_col = 0
        else:
            return False
        
        rook = self.get_piece(start_row, rook_col)
        if not rook or rook.type != 'rook' or rook.has_moved:
            return False
        
        # Проверка, что король не проходит через шах
        if self.is_square_attacked(start_row, start_col, self.current_turn):
            return False
        
        return True
    
    def is_square_attacked(self, row: int, col: int, by_color: str) -> bool:
        """Проверка, атакована ли клетка"""
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                piece = self.get_piece(r, c)
                if piece and piece.color == by_color:
                    # Временно убираем фигуру с целевой клетки для проверки
                    temp = self.get_piece(row, col)
                    self.board[row][col] = None
                    if self.is_valid_piece_move(piece, (r, c), (row, col)):
                        self.board[row][col] = temp
                        return True
                    self.board[row][col] = temp
        return False
    
    def would_be_in_check(self, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        """Проверка, будет ли король под шахом после хода"""
        # Сохраняем состояние
        start_row, start_col = start
        end_row, end_col = end
        piece = self.board[start_row][start_col]
        target = self.board[end_row][end_col]
        
        # Делаем ход
        self.board[end_row][end_col] = piece
        self.board[start_row][start_col] = None
        
        # Обновляем позицию короля если нужно
        if piece.type == 'king':
            if piece.color == 'white':
                king_pos = (end_row, end_col)
            else:
                king_pos = (end_row, end_col)
        else:
            king_pos = self.white_king_pos if self.current_turn == 'white' else self.black_king_pos
        
        # Проверяем шах
        opponent_color = 'black' if self.current_turn == 'white' else 'white'
        in_check = self.is_square_attacked(king_pos[0], king_pos[1], opponent_color)
        
        # Восстанавливаем состояние
        self.board[start_row][start_col] = piece
        self.board[end_row][end_col] = target
        
        return in_check
    
    def make_move(self, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        """Выполнить ход"""
        if not self.is_valid_move(start, end):
            return False
        
        start_row, start_col = start
        end_row, end_col = end
        piece = self.board[start_row][start_col]
        captured = self.board[end_row][end_col]
        
        # Сохраняем ход в историю
        move_notation = self.get_move_notation(start, end, captured)
        self.move_history.append({
            'start': start,
            'end': end,
            'piece': piece.type,
            'color': piece.color,
            'captured': captured.type if captured else None,
            'notation': move_notation
        })
        
        # Выполняем ход
        self.board[end_row][end_col] = piece
        self.board[start_row][start_col] = None
        piece.has_moved = True
        
        # Обновляем позицию короля
        if piece.type == 'king':
            if piece.color == 'white':
                self.white_king_pos = (end_row, end_col)
            else:
                self.black_king_pos = (end_row, end_col)
        
        # Рокировка
        if piece.type == 'king' and abs(end_col - start_col) == 2:
            if end_col == 6:  # Короткая
                rook = self.board[start_row][7]
                self.board[start_row][5] = rook
                self.board[start_row][7] = None
            elif end_col == 2:  # Длинная
                rook = self.board[start_row][0]
                self.board[start_row][3] = rook
                self.board[start_row][0] = None
        
        # Превращение пешки
        if piece.type == 'pawn' and (end_row == 0 or end_row == 7):
            self.board[end_row][end_col] = Piece(piece.color, 'queen')
        
        # Проверяем шах и мат
        self.current_turn = 'black' if self.current_turn == 'white' else 'white'
        self.update_check_status()
        self.check_game_over()
        
        return True
    
    def get_move_notation(self, start: Tuple[int, int], end: Tuple[int, int], captured: Optional[Piece]) -> str:
        """Получить нотацию хода"""
        files = 'abcdefgh'
        ranks = '87654321'
        start_file, start_rank = files[start[1]], ranks[start[0]]
        end_file, end_rank = files[end[1]], ranks[end[0]]
        
        piece = self.get_piece(start[0], start[1])
        if captured:
            return f"{piece.type[0].upper()}{start_file}{start_rank}x{end_file}{end_rank}"
        return f"{piece.type[0].upper()}{start_file}{start_rank}-{end_file}{end_rank}"
    
    def update_check_status(self):
        """Обновить статус шаха"""
        white_king = self.white_king_pos
        black_king = self.black_king_pos
        
        self.in_check['white'] = self.is_square_attacked(white_king[0], white_king[1], 'black')
        self.in_check['black'] = self.is_square_attacked(black_king[0], black_king[1], 'white')
    
    def check_game_over(self):
        """Проверка окончания игры"""
        if not self.has_valid_moves():
            if self.in_check[self.current_turn]:
                self.game_over = True
                self.winner = 'black' if self.current_turn == 'white' else 'white'
            else:
                self.game_over = True
                self.winner = 'draw'
    
    def has_valid_moves(self) -> bool:
        """Проверка наличия валидных ходов"""
        for r1 in range(BOARD_SIZE):
            for c1 in range(BOARD_SIZE):
                piece = self.get_piece(r1, c1)
                if piece and piece.color == self.current_turn:
                    for r2 in range(BOARD_SIZE):
                        for c2 in range(BOARD_SIZE):
                            if self.is_valid_move((r1, c1), (r2, c2)):
                                return True
        return False
    
    def get_all_moves(self, color: str) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """Получить все возможные ходы для цвета"""
        moves = []
        for r1 in range(BOARD_SIZE):
            for c1 in range(BOARD_SIZE):
                piece = self.get_piece(r1, c1)
                if piece and piece.color == color:
                    for r2 in range(BOARD_SIZE):
                        for c2 in range(BOARD_SIZE):
                            if self.is_valid_move((r1, c1), (r2, c2)):
                                moves.append(((r1, c1), (r2, c2)))
        return moves
    
    def evaluate_position(self) -> int:
        """Оценка позиции для ИИ"""
        piece_values = {'pawn': 10, 'knight': 30, 'bishop': 30, 'rook': 50, 'queen': 90, 'king': 900}
        score = 0
        
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                piece = self.get_piece(r, c)
                if piece:
                    value = piece_values[piece.type]
                    if piece.color == 'white':
                        score += value
                    else:
                        score -= value
        
        return score

class SimpleAI:
    def __init__(self, difficulty: int = 2):
        self.difficulty = difficulty  # 1-легкий, 2-средний, 3-сложный
    
    def get_move(self, board: ChessBoard) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """Получить ход от ИИ"""
        moves = board.get_all_moves('black')
        if not moves:
            return None
        
        if self.difficulty == 1:
            # Легкий: случайный ход
            return random.choice(moves) if moves else None
        elif self.difficulty == 2:
            # Средний: выбирает лучший ход по оценке
            best_move = None
            best_score = float('-inf')
            
            for start, end in moves:
                # Делаем временный ход
                temp_board = self.simulate_move(board, start, end)
                score = temp_board.evaluate_position()
                
                if score > best_score:
                    best_score = score
                    best_move = (start, end)
            
            return best_move if best_move else moves[0]
        else:
            # Сложный: минимакс с небольшой глубиной
            return self.minimax_move(board, 2)
    
    def simulate_move(self, board: ChessBoard, start: Tuple[int, int], end: Tuple[int, int]) -> ChessBoard:
        """Симуляция хода на копии доски"""
        import copy
        new_board = copy.deepcopy(board)
        new_board.make_move(start, end)
        return new_board
    
    def minimax_move(self, board: ChessBoard, depth: int) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """Минимакс алгоритм"""
        moves = board.get_all_moves('black')
        if not moves:
            return moves[0] if moves else None
        
        best_move = moves[0]
        best_score = float('-inf')
        
        for move in moves:
            temp_board = self.simulate_move(board, move[0], move[1])
            score = self.minimax(temp_board, depth - 1, False)
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move
    
    def minimax(self, board: ChessBoard, depth: int, maximizing: bool) -> int:
        """Минимакс рекурсия"""
        if depth == 0 or board.game_over:
            return board.evaluate_position()
        
        if maximizing:
            max_score = float('-inf')
            moves = board.get_all_moves('black')
            for move in moves:
                temp_board = self.simulate_move(board, move[0], move[1])
                score = self.minimax(temp_board, depth - 1, False)
                max_score = max(max_score, score)
            return max_score
        else:
            min_score = float('inf')
            moves = board.get_all_moves('white')
            for move in moves:
                temp_board = self.simulate_move(board, move[0], move[1])
                score = self.minimax(temp_board, depth - 1, True)
                min_score = min(min_score, score)
            return min_score

class ChessGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Шахматы")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 18)
        
        self.board = ChessBoard()
        self.selected_square = None
        self.possible_moves = []
        self.last_move = None
        
        # Таймеры
        self.white_time = 600  # 10 минут в секундах
        self.black_time = 600
        self.timer_start = time.time()
        self.timer_running = True
        
        # ИИ
        self.ai_enabled = True
        self.ai_difficulty = 2  # 1-легкий, 2-средний, 3-сложный
        self.ai = SimpleAI(difficulty=self.ai_difficulty)
        self.ai_thinking = False
        self.show_difficulty_menu = False
        
        # Анимации
        self.animations = []
        self.animating_piece = None
        self.animation_start = None
        self.animation_duration = 300  # миллисекунды
        self.animation_start_pos = None
        self.animation_end_pos = None
        
        self.piece_images = {}
        self.load_piece_images()
        
        # Звуки
        self.sounds = {}
        self.load_sounds()
        
        # UI
        self.show_history = True
        self.button_rects = {}  # Для хранения позиций кнопок
        self.pending_move = None  # Ожидающий ход для выполнения после анимации
        
    def load_piece_images(self):
        """Загрузка изображений фигур"""
        # Пытаемся загрузить из интернета или используем Unicode
        piece_types = ['king', 'queen', 'rook', 'bishop', 'knight', 'pawn']
        colors = ['white', 'black']
        
        for color in colors:
            for piece_type in piece_types:
                key = f"{color}_{piece_type}"
                # Попытка загрузить изображение
                image_path = f"pieces/{key}.png"
                if os.path.exists(image_path):
                    try:
                        self.piece_images[key] = pygame.image.load(image_path)
                        self.piece_images[key] = pygame.transform.scale(
                            self.piece_images[key], (SQUARE_SIZE - 10, SQUARE_SIZE - 10)
                        )
                    except:
                        self.piece_images[key] = None
                else:
                    self.piece_images[key] = None
    
    def load_sounds(self):
        """Загрузка звуков"""
        sound_files = {
            'move': 'sounds/move.wav',
            'capture': 'sounds/capture.wav',
            'check': 'sounds/check.wav',
            'checkmate': 'sounds/checkmate.wav'
        }
        
        for name, path in sound_files.items():
            if os.path.exists(path):
                try:
                    self.sounds[name] = pygame.mixer.Sound(path)
                except:
                    self.sounds[name] = None
            else:
                self.sounds[name] = None
    
    def play_sound(self, sound_name: str):
        """Воспроизвести звук"""
        if sound_name in self.sounds and self.sounds[sound_name]:
            try:
                self.sounds[sound_name].play()
            except:
                pass
    
    def get_square_from_pos(self, pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Получить координаты клетки из позиции мыши"""
        x, y = pos
        if x < BOARD_WIDTH and y < BOARD_HEIGHT:
            col = x // SQUARE_SIZE
            row = y // SQUARE_SIZE
            return (row, col)
        return None
    
    def draw_board(self):
        """Отрисовка доски"""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                x = col * SQUARE_SIZE
                y = row * SQUARE_SIZE
                
                # Цвет клетки
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(self.screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))
                
                # Подсветка последнего хода
                if self.last_move:
                    if (row, col) in [self.last_move[0], self.last_move[1]]:
                        highlight = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
                        highlight.set_alpha(100)
                        highlight.fill(YELLOW)
                        self.screen.blit(highlight, (x, y))
                
                # Подсветка шаха
                if self.board.in_check['white'] and (row, col) == self.board.white_king_pos:
                    highlight = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
                    highlight.set_alpha(150)
                    highlight.fill(RED)
                    self.screen.blit(highlight, (x, y))
                if self.board.in_check['black'] and (row, col) == self.board.black_king_pos:
                    highlight = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
                    highlight.set_alpha(150)
                    highlight.fill(RED)
                    self.screen.blit(highlight, (x, y))
                
                # Подсветка выбранной клетки
                if self.selected_square == (row, col):
                    highlight = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
                    highlight.set_alpha(150)
                    highlight.fill(SELECTED_HIGHLIGHT[:3])
                    self.screen.blit(highlight, (x, y))
                
                # Подсветка возможных ходов
                if (row, col) in self.possible_moves:
                    target = self.board.get_piece(row, col)
                    center_x = int(x + SQUARE_SIZE // 2)
                    center_y = int(y + SQUARE_SIZE // 2)
                    if target:
                        # Атака - красный круг
                        pygame.draw.circle(self.screen, RED, 
                                         (center_x, center_y), 
                                         int(SQUARE_SIZE // 2 - 5), 3)
                    else:
                        # Обычный ход - зеленый круг
                        pygame.draw.circle(self.screen, GREEN, 
                                         (center_x, center_y), 
                                         10)
    
    def start_animation(self, start: Tuple[int, int], end: Tuple[int, int]):
        """Начать анимацию движения фигуры"""
        start_row, start_col = start
        end_row, end_col = end
        
        self.animating_piece = self.board.get_piece(start_row, start_col)
        self.animation_start = time.time() * 1000  # в миллисекундах
        self.animation_start_pos = (
            start_col * SQUARE_SIZE + SQUARE_SIZE // 2,
            start_row * SQUARE_SIZE + SQUARE_SIZE // 2
        )
        self.animation_end_pos = (
            end_col * SQUARE_SIZE + SQUARE_SIZE // 2,
            end_row * SQUARE_SIZE + SQUARE_SIZE // 2
        )
    
    def update_animation(self):
        """Обновить анимацию"""
        if not self.animating_piece:
            return False
        
        current_time = time.time() * 1000
        elapsed = current_time - self.animation_start
        
        if elapsed >= self.animation_duration:
            # Анимация завершена
            self.animating_piece = None
            return True
        
        return False
    
    def get_animation_pos(self) -> Optional[Tuple[int, int]]:
        """Получить текущую позицию анимируемой фигуры"""
        if not self.animating_piece or not self.animation_start:
            return None
        
        current_time = time.time() * 1000
        elapsed = current_time - self.animation_start
        progress = min(elapsed / self.animation_duration, 1.0)
        
        # Плавная интерполяция (ease-out)
        smooth_progress = progress * (2 - progress)
        
        x = int(self.animation_start_pos[0] + 
                (self.animation_end_pos[0] - self.animation_start_pos[0]) * smooth_progress)
        y = int(self.animation_start_pos[1] + 
                (self.animation_end_pos[1] - self.animation_start_pos[1]) * smooth_progress)
        
        return (x, y)
    
    def draw_pieces(self):
        """Отрисовка фигур"""
        anim_pos = self.get_animation_pos()
        anim_start_square = self.pending_move[0] if self.pending_move else None
        
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board.get_piece(row, col)
                
                # Пропускаем анимируемую фигуру на стартовой позиции
                if anim_start_square and (row, col) == anim_start_square and anim_pos:
                    continue
                
                if piece:
                    x = col * SQUARE_SIZE + SQUARE_SIZE // 2
                    y = row * SQUARE_SIZE + SQUARE_SIZE // 2
                    
                    key = f"{piece.color}_{piece.type}"
                    if key in self.piece_images and self.piece_images[key]:
                        # Используем изображение
                        img = self.piece_images[key]
                        img_rect = img.get_rect(center=(x, y))
                        self.screen.blit(img, img_rect)
                    else:
                        # Используем Unicode символ
                        symbol = piece.get_symbol()
                        text = self.big_font.render(symbol, True, 
                                                   WHITE if piece.color == 'white' else BLACK)
                        text_rect = text.get_rect(center=(x, y))
                        self.screen.blit(text, text_rect)
        
        # Отрисовка анимируемой фигуры поверх всего
        if self.animating_piece and anim_pos:
            key = f"{self.animating_piece.color}_{self.animating_piece.type}"
            x, y = anim_pos
            if key in self.piece_images and self.piece_images[key]:
                img = self.piece_images[key]
                img_rect = img.get_rect(center=(x, y))
                self.screen.blit(img, img_rect)
            else:
                symbol = self.animating_piece.get_symbol()
                text = self.big_font.render(symbol, True, 
                                           WHITE if self.animating_piece.color == 'white' else BLACK)
                text_rect = text.get_rect(center=(x, y))
                self.screen.blit(text, text_rect)
    
    def draw_ui(self):
        """Отрисовка интерфейса"""
        panel_x = BOARD_WIDTH
        panel_y = 0
        
        # Фон панели
        pygame.draw.rect(self.screen, DARK_GRAY, (panel_x, 0, PANEL_WIDTH, WINDOW_HEIGHT))
        
        y_offset = 20
        
        # Текущий ход
        turn_text = f"Ход: {'Белые' if self.board.current_turn == 'white' else 'Черные'}"
        text = self.font.render(turn_text, True, WHITE)
        self.screen.blit(text, (panel_x + 10, y_offset))
        y_offset += 40
        
        # Таймеры
        if self.timer_running and not self.board.game_over:
            if self.board.current_turn == 'white':
                elapsed = time.time() - self.timer_start
                self.white_time -= elapsed
                self.timer_start = time.time()
            else:
                elapsed = time.time() - self.timer_start
                self.black_time -= elapsed
                self.timer_start = time.time()
        
        white_min = int(self.white_time // 60)
        white_sec = int(self.white_time % 60)
        black_min = int(self.black_time // 60)
        black_sec = int(self.black_time % 60)
        
        white_timer = f"Белые: {white_min:02d}:{white_sec:02d}"
        black_timer = f"Черные: {black_min:02d}:{black_sec:02d}"
        
        if self.white_time <= 0 or self.black_time <= 0:
            self.board.game_over = True
            if self.white_time <= 0:
                self.board.winner = 'black'
            else:
                self.board.winner = 'white'
        
        text = self.small_font.render(white_timer, True, WHITE)
        self.screen.blit(text, (panel_x + 10, y_offset))
        y_offset += 30
        
        text = self.small_font.render(black_timer, True, WHITE)
        self.screen.blit(text, (panel_x + 10, y_offset))
        y_offset += 50
        
        # Статус
        if self.board.in_check['white']:
            text = self.font.render("ШАХ белым!", True, RED)
            self.screen.blit(text, (panel_x + 10, y_offset))
            y_offset += 40
        if self.board.in_check['black']:
            text = self.font.render("ШАХ черным!", True, RED)
            self.screen.blit(text, (panel_x + 10, y_offset))
            y_offset += 40
        
        if self.board.game_over:
            if self.board.winner == 'white':
                text = self.big_font.render("ПОБЕДА БЕЛЫХ!", True, GREEN)
            elif self.board.winner == 'black':
                text = self.big_font.render("ПОБЕДА ЧЕРНЫХ!", True, GREEN)
            else:
                text = self.big_font.render("НИЧЬЯ!", True, YELLOW)
            self.screen.blit(text, (panel_x + 10, y_offset))
            y_offset += 60
        
        # Кнопки
        button_y = WINDOW_HEIGHT - 250
        buttons = [
            ("Новая игра", "new_game"),
            ("Сложность ИИ", "difficulty"),
            ("Отменить ход", "undo"),
            ("Сохранить", "save"),
            ("Загрузить", "load"),
        ]
        
        self.button_rects = {}
        for i, (label, action) in enumerate(buttons):
            btn_y = button_y + i * 40
            btn_rect = pygame.Rect(panel_x + 10, btn_y, PANEL_WIDTH - 20, 35)
            self.button_rects[action] = btn_rect
            
            # Подсветка при наведении
            mouse_pos = pygame.mouse.get_pos()
            color = WHITE if btn_rect.collidepoint(mouse_pos) else LIGHT_GRAY
            
            pygame.draw.rect(self.screen, color, btn_rect)
            pygame.draw.rect(self.screen, BLACK, btn_rect, 2)
            text = self.small_font.render(label, True, BLACK)
            text_rect = text.get_rect(center=(panel_x + PANEL_WIDTH // 2, btn_y + 17))
            self.screen.blit(text, text_rect)
        
        # Показываем текущую сложность
        difficulty_names = {1: "Легкий", 2: "Средний", 3: "Сложный"}
        diff_text = f"Сложность: {difficulty_names.get(self.ai_difficulty, 'Средний')}"
        text = self.small_font.render(diff_text, True, YELLOW)
        self.screen.blit(text, (panel_x + 10, button_y - 25))
        
        # Меню выбора сложности
        if self.show_difficulty_menu:
            menu_y = button_y - 120
            pygame.draw.rect(self.screen, DARK_GRAY, 
                           (panel_x + 10, menu_y - 100, PANEL_WIDTH - 20, 100))
            pygame.draw.rect(self.screen, WHITE, 
                           (panel_x + 10, menu_y - 100, PANEL_WIDTH - 20, 100), 2)
            
            for i in range(1, 4):
                diff_y = menu_y - 100 + (4-i) * 30
                diff_rect = pygame.Rect(panel_x + 15, diff_y, PANEL_WIDTH - 30, 25)
                color = GREEN if i == self.ai_difficulty else LIGHT_GRAY
                pygame.draw.rect(self.screen, color, diff_rect)
                text = self.small_font.render(difficulty_names[i], True, BLACK)
                self.screen.blit(text, (panel_x + 20, diff_y + 5))
        
        # История ходов
        if self.show_history:
            y_offset = 300
            text = self.small_font.render("История ходов:", True, WHITE)
            self.screen.blit(text, (panel_x + 10, y_offset))
            y_offset += 25
            
            for i, move in enumerate(self.board.move_history[-10:]):  # Последние 10 ходов
                move_text = f"{i + 1}. {move['notation']}"
                text = self.small_font.render(move_text, True, LIGHT_GRAY)
                self.screen.blit(text, (panel_x + 10, y_offset))
                y_offset += 20
                if y_offset > WINDOW_HEIGHT - 250:
                    break
    
    def new_game(self):
        """Новая игра"""
        self.board = ChessBoard()
        self.selected_square = None
        self.possible_moves = []
        self.last_move = None
        self.white_time = 600
        self.black_time = 600
        self.timer_start = time.time()
        self.timer_running = True
    
    def undo_move(self):
        """Отменить последний ход"""
        if len(self.board.move_history) >= 2:  # Отменяем ход игрока и ИИ
            # Упрощенная версия - просто новая игра
            # В полной версии нужно восстановить состояние доски
            self.new_game()
    
    def save_game(self):
        """Сохранить игру"""
        game_data = {
            'board_state': self.serialize_board(),
            'current_turn': self.board.current_turn,
            'move_history': self.board.move_history,
            'white_time': self.white_time,
            'black_time': self.black_time
        }
        
        with open('chess_save.json', 'w', encoding='utf-8') as f:
            json.dump(game_data, f, indent=2, ensure_ascii=False)
    
    def load_game(self):
        """Загрузить игру"""
        if os.path.exists('chess_save.json'):
            try:
                with open('chess_save.json', 'r', encoding='utf-8') as f:
                    game_data = json.load(f)
                # Восстановление состояния (упрощенная версия)
                self.new_game()
            except:
                pass
    
    def serialize_board(self):
        """Сериализация доски"""
        # Упрощенная версия
        return []
    
    def handle_click(self, pos: Tuple[int, int]):
        """Обработка клика мыши"""
        x, y = pos
        
        # Проверка клика по кнопкам
        if BOARD_WIDTH < x < WINDOW_WIDTH:
            for action, rect in self.button_rects.items():
                if rect.collidepoint(pos):
                    if action == "new_game":
                        self.new_game()
                    elif action == "difficulty":
                        self.show_difficulty_menu = not self.show_difficulty_menu
                    elif action == "undo":
                        self.undo_move()
                    elif action == "save":
                        self.save_game()
                    elif action == "load":
                        self.load_game()
                    return
        
        # Обработка меню выбора сложности
        if self.show_difficulty_menu:
            panel_x = BOARD_WIDTH
            menu_y = WINDOW_HEIGHT - 250
            for i in range(1, 4):
                diff_rect = pygame.Rect(panel_x + 10, menu_y - 40 - (4-i) * 40, PANEL_WIDTH - 20, 35)
                if diff_rect.collidepoint(pos):
                    self.ai_difficulty = i
                    self.ai = SimpleAI(difficulty=i)
                    self.show_difficulty_menu = False
                    return
        
        # Игровые клики только если не закончена игра и ход белых
        if self.board.game_over or self.board.current_turn != 'white' or self.animating_piece:
            return
        
        square = self.get_square_from_pos(pos)
        if square is None:
            return
        
        row, col = square
        
        if self.selected_square is None:
            # Выбор фигуры
            piece = self.board.get_piece(row, col)
            if piece and piece.color == self.board.current_turn:
                self.selected_square = (row, col)
                self.possible_moves = []
                # Находим все возможные ходы
                for r in range(BOARD_SIZE):
                    for c in range(BOARD_SIZE):
                        if self.board.is_valid_move(self.selected_square, (r, c)):
                            self.possible_moves.append((r, c))
        else:
            # Попытка сделать ход
            if (row, col) in self.possible_moves:
                start_square = self.selected_square
                end_square = (row, col)
                
                # Начинаем анимацию
                self.start_animation(start_square, end_square)
                
                # Ход будет выполнен после анимации
                self.pending_move = (start_square, end_square)
                
                self.selected_square = None
                self.possible_moves = []
            else:
                # Выбор другой фигуры
                piece = self.board.get_piece(row, col)
                if piece and piece.color == self.board.current_turn:
                    self.selected_square = (row, col)
                    self.possible_moves = []
                    for r in range(BOARD_SIZE):
                        for c in range(BOARD_SIZE):
                            if self.board.is_valid_move(self.selected_square, (r, c)):
                                self.possible_moves.append((r, c))
                else:
                    self.selected_square = None
                    self.possible_moves = []
    
    def execute_pending_move(self):
        """Выполнить ожидающий ход после завершения анимации"""
        if not self.pending_move:
            return
        
        start, end = self.pending_move
        if self.board.make_move(start, end):
            self.last_move = (start, end)
            self.play_sound('move')
            if self.board.get_piece(end[0], end[1]):  # Взятие
                self.play_sound('capture')
            if self.board.in_check[self.board.current_turn]:
                self.play_sound('check')
            if self.board.game_over:
                self.play_sound('checkmate')
            
            # Ход ИИ (выполняется сразу, без анимации для скорости)
            if self.ai_enabled and not self.board.game_over:
                self.ai_thinking = True
                # Небольшая задержка для реалистичности
                pygame.time.wait(200)
                ai_move = self.ai.get_move(self.board)
                if ai_move and self.board.make_move(ai_move[0], ai_move[1]):
                    self.last_move = ai_move
                    self.play_sound('move')
                    if self.board.get_piece(ai_move[1][0], ai_move[1][1]):
                        self.play_sound('capture')
                    if self.board.in_check[self.board.current_turn]:
                        self.play_sound('check')
                    if self.board.game_over:
                        self.play_sound('checkmate')
                self.ai_thinking = False
        
        self.pending_move = None
    
    def run(self):
        """Главный игровой цикл"""
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Левая кнопка мыши
                        self.handle_click(event.pos)
            
            # Обновление анимации
            if self.animating_piece:
                if self.update_animation():
                    # Анимация завершена, выполняем ход
                    self.execute_pending_move()
            
            # Отрисовка
            self.screen.fill(BLACK)
            self.draw_board()
            self.draw_pieces()
            self.draw_ui()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = ChessGame()
    game.run()

