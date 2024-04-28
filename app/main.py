import pygame
import sys

from pygame.locals import *
from llm import TextGameEngine, InventoryEngine, InventoryItem

# Constants
FPS = 30
BG_COLOR = pygame.Color('black')
TEXT_COLOR = pygame.Color('white')
BORDER_COLOR = pygame.Color('gray')
BORDER_WIDTH = 4
FONT_NAME = pygame.font.match_font('courier')  # Monospace font similar to DOS fonts

# Initialize Pygame
pygame.init()
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w // 2, info.current_h // 2
screen = pygame.display.set_mode((WIDTH, HEIGHT), RESIZABLE)
pygame.display.set_caption("Text-based DOS Game")
clock = pygame.time.Clock()

def get_font(size):
    return pygame.font.Font(FONT_NAME, size)

def draw_text(surface, text, position, color, font, wrap_width):
    words = text.split()
    space_width, line_height = font.size(" ")
    x, y = position
    start_x = position[0] + 10  # Adding left margin

    current_line = []
    current_line_width = 0

    for word in words:
        word_surface = font.render(word, True, color)
        word_width, word_height = word_surface.get_size()

        if current_line_width + word_width > wrap_width:
            for word_surf in current_line:
                surface.blit(word_surf[0], (word_surf[1], y))
            y += line_height
            current_line = []
            current_line_width = 0
            x = start_x

        current_line.append((word_surface, x))
        current_line_width += word_width + space_width
        x += word_width + space_width

    for word_surf in current_line:
        surface.blit(word_surf[0], (word_surf[1], y))

    return y + line_height
def show_image(screen, image_path, position, size):
    try:
        # Load the image from the path
        image = pygame.image.load(image_path)

        # Get the original dimensions of the image
        original_width, original_height = image.get_size()

        # Calculate the scaling factor while maintaining the aspect ratio
        width_ratio = size[0] / original_width
        height_ratio = size[1] / original_height
        scale_ratio = min(width_ratio, height_ratio)  # Use the smaller ratio to ensure the image fits within the space

        # Calculate the new dimensions based on the scaling ratio
        new_width = int(original_width * scale_ratio)
        new_height = int(original_height * scale_ratio)

        # Scale the image to the new dimensions
        image = pygame.transform.scale(image, (new_width, new_height))

        # Calculate the position to center the image in the designated area
        new_x = position[0] + (size[0] - new_width) // 2
        new_y = position[1] + (size[1] - new_height) // 2

        # Blit the image to the screen at the new position
        screen.blit(image, (new_x, new_y))
    except pygame.error as e:
        print(f"Failed to load image: {e}")

def estimate_lines(text, font, wrap_width):
    words = text.split()
    space_width, line_height = font.size(" ")
    current_line_width = 0
    line_count = 1  # Start with one line

    for word in words:
        word_width, _ = font.size(word)
        if current_line_width + word_width > wrap_width:
            line_count += 1
            current_line_width = 0  # Reset line width for the new line
        current_line_width += word_width + space_width

    return line_count

def update_text_buffer(text_buffer, new_text, max_lines):
    # Add new text
    text_buffer.extend(new_text.split('\n'))

    # Check if buffer exceeds maximum lines
    while len(text_buffer) > max_lines:
        text_buffer.pop(0)  # Remove the oldest line to maintain size

def draw_bordered_box(surface, rect, color, border_width):
    pygame.draw.rect(surface, color, rect, border_width)


# Inventory Item class



def draw_score(surface, score, position, color, font, area_width):
    score_text = f"Score: {score}"
    score_surface = font.render(score_text, True, color)
    text_width = score_surface.get_width()
    # Calculate new x position to center the score in the given area
    new_x = position[0] + (area_width - text_width) // 2
    score_rect = score_surface.get_rect(topright=(new_x, position[1]))
    surface.blit(score_surface, score_rect)


import pygame


def draw_label(surface, name, description, font, position, max_width, image_path):
    try:
        # Load and scale the image
        image = pygame.image.load(image_path)
        image_width, image_height = image.get_size()

        # Calculate scale to maintain aspect ratio
        scale = min(max_width / image_width, (HEIGHT // 3) / image_height)
        scaled_width = int(image_width * scale)
        scaled_height = int(image_height * scale)
        image = pygame.transform.scale(image, (scaled_width, scaled_height))
        image_rect = image.get_rect(center=(WIDTH // 2, HEIGHT // 2 - scaled_height // 2))
    except pygame.error as e:
        print(f"Failed to load image: {e}")
        return

    # Prepare text for name and description to calculate total height
    name_surface = font.render(name, True, TEXT_COLOR)
    name_rect = name_surface.get_rect(centerx=WIDTH // 2, top=image_rect.bottom)

    # Word wrapping calculation
    words = description.split(' ')
    space_width, line_height = font.size(' ')
    line_words = []
    line_width = 0
    lines = []

    for word in words:
        word_surface = font.render(word, True, TEXT_COLOR)
        word_width, word_height = word_surface.get_size()
        if line_width + word_width > max_width:
            lines.append((line_words, line_width))
            line_words = [word]
            line_width = word_width + space_width
        else:
            line_words.append(word)
            line_width += word_width + space_width
    lines.append((line_words, line_width))  # Append the last line

    # Calculate overall height of all text elements
    total_text_height = len(lines) * line_height
    total_card_height = HEIGHT - 25  # plus margins

    # Calculate card position to ensure it is centered
    card_rect = pygame.Rect((WIDTH - max_width) // 2, max(0, HEIGHT // 2 - total_card_height // 2), max_width,
                            total_card_height)

    # Draw black background
    pygame.draw.rect(surface, (0, 0, 0), card_rect)  # Filling with black

    # Blit the image and texts
    surface.blit(image, image_rect)
    surface.blit(name_surface, name_rect)

    text_top = name_rect.bottom + 10  # Start text below the name
    for line_words, line_width in lines:
        line_text = ' '.join(line_words)
        line_surface = font.render(line_text, True, TEXT_COLOR)
        line_rect = line_surface.get_rect(centerx=WIDTH // 2, top=text_top)
        surface.blit(line_surface, line_rect)
        text_top += line_height

    # Draw border around the card
    pygame.draw.rect(surface, BORDER_COLOR, card_rect, 1)  # Drawing border


def main():
    global WIDTH, HEIGHT, screen
    game_engine = TextGameEngine()
    inventory_engine = InventoryEngine(game_engine.api_comms, 6)
    # inventory = Inventory(6)
    game_engine.inventory_engine = inventory_engine
    # inventory_engine.inventory = inventory
    start_items = inventory_engine.get_start_items()

    font_size = HEIGHT // 30
    font = get_font(font_size)
    input_text = ''
    base_y = HEIGHT - font_size * 2  # Position of the input area

    # Adjust the width and position calculations
    text_area_width = int(WIDTH * 0.68)
    image_area_width = WIDTH - text_area_width - 20
    score_position = (text_area_width + 10, 10)  # Starting x position of the image area, y position remains at the top
    score = 0
    image_position = (text_area_width + 10, 20)
    image_size = (image_area_width - 20, HEIGHT - 240)
    inventory_area_size = (image_area_width - 20, 200)
    inventory_position = (image_position[0], HEIGHT - inventory_area_size[1] - 20)


    running = True
    text_buffer = []
    image_path = None  # Path to the current image
    #system_response, image_path, _ = game_engine.generate_response()
    if image_path is not None:
        # image.save('current.png', "PNG")
        # image_path = 'current.png'
        show_image(screen, image_path, image_position, image_size)
    update_text_buffer(text_buffer, "> " + input_text, 8)
    #update_text_buffer(text_buffer, system_response, 8)



    # Add example inventory items for testing
    # inventory.add_item(InventoryItem("Example 1", "myapp.png"))
    # inventory.add_item(InventoryItem("Example 2", "myapp.png"))
    for item in start_items:
        inventory_engine.add_item(InventoryItem(item['name'], item['description'], item['image']))
    while running:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(BG_COLOR)
        inventory_engine.draw_inventory(screen, inventory_position, inventory_area_size)
        hovered_item_name, hovered_item_description, hovered_item_image = inventory_engine.get_item_at_pos(mouse_pos)

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                #screen = pygame.display.set_mode((WIDTH, HEIGHT), RESIZABLE)
                font = get_font(font_size)

                text_area_width = int(WIDTH * 0.68)
                image_area_width = WIDTH - text_area_width - 20

                image_position = (text_area_width + 10, 20)
                score_position = (text_area_width + 10, 10)  # Starting x position of the image area, y position remains at the top

                image_size = (image_area_width - 20, HEIGHT - 240)
                inventory_area_size = (image_area_width - 20, 200)
                inventory_position = (image_position[0], HEIGHT - inventory_area_size[1] - 20)

            elif event.type == KEYDOWN:
                if event.key == K_RETURN:
                    game_engine.add_user_message(input_text)
                    system_response, image_path, new_score = game_engine.generate_response()
                    if image_path is not None:
                        # image.save('current.png', "PNG")
                        # image_path = 'current.png'
                        show_image(screen, image_path, image_position, image_size)
                    if new_score is not None:
                        score += new_score
                    update_text_buffer(text_buffer, "> " + input_text, 8)
                    update_text_buffer(text_buffer, system_response, 8)
                    input_text = ''
                elif event.key == K_BACKSPACE:
                    input_text = input_text[:-1]
                elif event.key == pygame.K_f and (event.mod & pygame.KMOD_CTRL):
                    if screen.get_flags() & pygame.FULLSCREEN:
                        pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                    else:
                        pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
                else:
                    input_text += event.unicode



        draw_score(screen, score, score_position, TEXT_COLOR, font, image_area_width)

        y_offset = 20  # Top margin adjusted
        for text in text_buffer[-5:]:
            y_offset = draw_text(screen, text, (10, y_offset), TEXT_COLOR, font, text_area_width - 20)  # Left margin

        draw_text(screen, f"> {input_text}", (10, base_y), TEXT_COLOR, font, text_area_width - 20)  # Input field margin

        if image_path:
            show_image(screen, image_path, image_position, image_size)

        # Adjust border dimensions to fit within the window properly
        draw_bordered_box(screen, (10, 10, text_area_width, HEIGHT - 20), BORDER_COLOR, BORDER_WIDTH)
        draw_bordered_box(screen, (text_area_width + 10, 10, image_area_width - 20, HEIGHT - 20), BORDER_COLOR, BORDER_WIDTH)
        if hovered_item_name:
            draw_label(screen, hovered_item_name, hovered_item_description, font, mouse_pos, WIDTH / 3, hovered_item_image)  # Display name at mouse position

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
