import pygame
import sys
import random
import time
from ffpyplayer.player import MediaPlayer
from words import WORDS
from PIL import Image

# Initialize Pygame
pygame.init()

# Screen dimensions and grid settings
WIDTH, HEIGHT = 600, 400
CELL_SIZE = 50
ROWS, COLS = HEIGHT // CELL_SIZE, WIDTH // CELL_SIZE

# Colors
WHITE = (255, 255, 255)
BLACK = (100, 10, 0)
GRAY = (169, 169, 169)
GREEN = (100, 0, 0)
RED = (255, 0, 0)
REVEALED_COLOR = (200, 200, 200)

# Load flag and mine sprites
flag_img = pygame.image.load("assets/flag.png")
mine_img = pygame.image.load("assets/mine.png")

# Scale sprites to fit the cells
flag_img = pygame.transform.scale(flag_img, (50, 50))
mine_img = pygame.transform.scale(mine_img, (CELL_SIZE, CELL_SIZE))

# Load sounds and background music
explosion_sound = pygame.mixer.Sound("assets/explosion.wav")
wrong = pygame.mixer.Sound("assets/wrong.mp3")
yey = pygame.mixer.Sound("assets/yey.mp3")
menu_music = 'assets/bg.mp3'  # Background music for the menu
gameplay_music = 'assets/bgm.mp3'  # Background music for the gameplay

# Setup display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("POP A QUEST")

# Game variables
tiles = [[0 for _ in range(COLS)] for _ in range(ROWS)]  # 0: hidden, 1: revealed, 2: flagged, 3: mine, 4: clicked mine
mine_count = 10  # Number of mines
game_over = False
victory = False
lives = 3  # Number of lives
life_images = [pygame.image.load(f"assets/life{i}.png") for i in range(1, 4)]
life_image = life_images[lives - 1]  # Initialize life image

# Word jumble variables
jumble_active = False
jumble_word = ""
correct_word = ""
user_input = ""
timer_start = 0

TIMER_LIMIT = 15  # 15 seconds

# Jumble word list
words_list = WORDS

# Helper function to jumble a word
def jumble_word_fn(word):
    char_list = list(word)
    random.shuffle(char_list)
    return ''.join(char_list)

# Place mines randomly
def place_mines():
    mine_positions = random.sample(range(ROWS * COLS), mine_count)
    for pos in mine_positions:
        row, col = divmod(pos, COLS)
        tiles[row][col] = 3  # 3 represents a mine

def count_mines_around(row, col):
    count = 0
    for r in range(row-1, row+2):
        for c in range(col-1, col+2):
            if 0 <= r < ROWS and 0 <= c < COLS and tiles[r][c] == 3:
                count += 1
    return count

def reveal_tile(row, col):
    global game_over, lives, life_image, jumble_active, jumble_word, correct_word, timer_start, user_input

    if game_over:  # Don't reveal any tiles if the game is over
        return

    if tiles[row][col] in (1, 2):  # Already revealed or flagged
        return
    
    if tiles[row][col] == 3:  # Mine hit
        # Trigger jumble word game
        jumble_active = True
        correct_word = random.choice(words_list)
        jumble_word = jumble_word_fn(correct_word)
        timer_start = time.time()  # Start the timer
        user_input = ""  # Reset user input
        return  # Don't reveal more tiles until bomb is solved or life is lost

    tiles[row][col] = 1  # Reveal the tile
    mines_around = count_mines_around(row, col)
    
    if mines_around == 0:  # If no surrounding mines, reveal adjacent tiles
        for r in range(row-1, row+2):
            for c in range(col-1, col+2):
                if 0 <= r < ROWS and 0 <= c < COLS:
                    reveal_tile(r, c)

    check_victory()
    
def slow_mine_reveal():
    for row in range(ROWS):
        for col in range(COLS):
            if tiles[row][col] == 3:
                explosion_sound.play()
                pygame.draw.rect(screen, REVEALED_COLOR, pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE))
                screen.blit(mine_img, (col * CELL_SIZE, row * CELL_SIZE))
                pygame.display.flip()
                pygame.time.wait(100)
                
def play_video(video_file):
    player = MediaPlayer(video_file)
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        frame, val = player.get_frame()
        if val == 'eof':
            break
        if frame is None:
            pygame.display.flip()
            clock.tick(30)
            continue
        
        img, _ = frame
        img_surface = pygame.image.frombuffer(img.to_bytearray()[0], img.get_size(), 'RGB')
        screen.blit(img_surface, (5,5))
        pygame.display.flip()
        clock.tick(10)


def check_victory():
    global victory
    total_cells = ROWS * COLS
    revealed_cells = sum(1 for row in tiles for cell in row if cell == 1)

    if revealed_cells == (total_cells - mine_count):
        print("You Win!")
        pygame.mixer.music.stop()
        play_video('assets/victory.mp4')
        # sys.exit()
        victory = True
        start_menu()

def draw_board():
    for row in range(ROWS):
        for col in range(COLS):
            x, y = col * CELL_SIZE, row * CELL_SIZE
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

            if tiles[row][col] == 0:
                pygame.draw.rect(screen, GRAY, rect)  # Hidden tiles
            elif tiles[row][col] == 1:
                pygame.draw.rect(screen, REVEALED_COLOR, rect)  # Revealed tiles
                mines_around = count_mines_around(row, col)
                if mines_around > 0:
                    font = pygame.font.Font(None, 24)
                    text = font.render(str(mines_around), True, BLACK)
                    screen.blit(text, (x + CELL_SIZE // 4, y + CELL_SIZE // 4))
            elif tiles[row][col] == 3:
                if game_over or victory:
                    font = pygame.font.Font(None, 24)
                    text = font.render('X', True, BLACK)
                    screen.blit(text, (x + CELL_SIZE // 4, y + CELL_SIZE // 4))
                else:
                    pygame.draw.rect(screen, GRAY, rect)  # Hidden mines
            elif tiles[row][col] == 4:
                pygame.draw.rect(screen, REVEALED_COLOR, rect)  # Make it revealed
                font = pygame.font.Font(None, 24)
                text = font.render('X', True, BLACK)
                screen.blit(text, (x + CELL_SIZE // 4, y + CELL_SIZE // 4))

    # Draw the grid lines
    for row in range(ROWS + 1):  # +1 to draw the bottom line
        pygame.draw.line(screen, BLACK, (0, row * CELL_SIZE), (WIDTH, row * CELL_SIZE))
    for col in range(COLS + 1):  # +1 to draw the right line
        pygame.draw.line(screen, BLACK, (col * CELL_SIZE, 0), (col * CELL_SIZE, HEIGHT))

def handle_click(x, y):
    col, row = x // CELL_SIZE, y // CELL_SIZE
    if 0 <= row < ROWS and 0 <= col < COLS:
        reveal_tile(row, col)

def draw_jumble():
    font = pygame.font.Font(None, 36)
    
    # Create Background
    rect = pygame.Rect(0, HEIGHT - 85, WIDTH, HEIGHT - 85)
    pygame.draw.rect(screen, BLACK, rect)
    
    # Display the jumbled word and user input
    jumble_text = font.render(f"Jumbled word: {jumble_word}", True, WHITE)
    input_text = font.render(f"Your input: {user_input}", True, WHITE)
    timer_text = font.render(f"Time left: {TIMER_LIMIT - int(time.time() - timer_start)}", True, WHITE)

    screen.blit(jumble_text, (10, HEIGHT - 80))
    screen.blit(input_text, (10, HEIGHT - 40))
    screen.blit(timer_text, (WIDTH - 200, HEIGHT - 80))
    
def game_loop():
    global game_over, victory, jumble_active, user_input, lives, life_image
    place_mines()
    pygame.mixer.music.load(gameplay_music)
    pygame.mixer.music.play(-1)

    running = True
    while running:
        screen.fill(GRAY)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and not game_over and not victory and not jumble_active:
                x, y = event.pos
                handle_click(x, y)
            if jumble_active and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if user_input.lower() == correct_word.lower():
                        yey.play()
                        jumble_active = False  # Bomb defused
                        print("Bomb defused!")
                    else:
                        wrong.play()
                        jumble_active = False  # Time's up, lose a life
                        lives -= 1
                        if lives > 0:
                            life_image = life_images[lives - 1]
                        else:
                            print("Game Over!")
                            slow_mine_reveal()
                            pygame.mixer.music.stop()
                            play_video('assets/over.mp4')
                            running = False
                            # sys.exit()
                            game_over = True
                            start_menu()
                            break
                elif event.key == pygame.K_BACKSPACE:
                    user_input = user_input[:-1]
                else:
                    user_input += event.unicode
        
        # Draw the game elements
        draw_board()
        
        # Draw life count
        screen.blit(life_image, (10, 10))

        if jumble_active:
            draw_jumble()
            if time.time() - timer_start > TIMER_LIMIT:
                wrong.play()
                jumble_active = False
                lives -= 1
                if lives > 0:
                    life_image = life_images[lives - 1]
                else:
                    print("Game Over!")
                    slow_mine_reveal()
                    pygame.mixer.music.stop()
                    play_video('assets/over.mp4')
                    running = False
                    # sys.exit()
                    game_over = True
                    start_menu()
                    break

        pygame.display.update()
        
def extract_gif_frames(gif_path):
    gif = Image.open(gif_path)
    frames = []
    try:
        while True:
            frame = gif.copy()
            frame = frame.convert("RGBA")  # Ensure RGBA mode for transparency
            frame = frame.resize((WIDTH, HEIGHT))  # Resize to match the window
            frames.append(pygame.image.fromstring(frame.tobytes(), frame.size, 'RGBA'))
            gif.seek(len(frames))  # Move to the next frame
    except EOFError:
        pass  # End of GIF
    return frames
        
def start_menu():
    # Load and extract GIF frames
    gif_frames = extract_gif_frames("assets/background.gif")  # Replace with your GIF file
    current_frame = 0
    total_frames = len(gif_frames)

    pygame.mixer.music.load(menu_music)  # Load menu music
    pygame.mixer.music.play(-1)  # Play background music on loop

    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if start_button_rect.collidepoint(x, y):
                    pygame.mixer.music.stop()
                    game_loop()
                elif exit_button_rect.collidepoint(x, y):
                    pygame.quit()
                    sys.exit()

        # Blit the current frame of the GIF
        screen.blit(gif_frames[current_frame], (0,0))

        # Update the frame index
        current_frame = (current_frame + 1) % total_frames

        # Draw start and quit buttons
        pygame.draw.rect(screen, BLACK, start_button_rect)
        pygame.draw.rect(screen, BLACK, exit_button_rect)

        # Render text with smaller font size
        font = pygame.font.Font(None, 36)  # Set font size to 36
        start_text = font.render('Start Game', True, WHITE)
        exit_text = font.render('Quit', True, WHITE)
        screen.blit(start_text, (start_button_rect.x + 10, start_button_rect.y + 10))
        screen.blit(exit_text, (exit_button_rect.x + 10, exit_button_rect.y + 10))

        pygame.display.flip()
        clock.tick(10)  # Control GIF frame rate (10 FPS)

# Initialize and draw the menu
start_button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 50)
exit_button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 10, 200, 50)
start_menu()
