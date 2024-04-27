import pygame
import sys

from pygame.locals import *
from llm import TextGameEngine, InventoryEngine

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
class InventoryItem:
    def __init__(self, name, description, image_path):
        self.name = name
        self.description = description
        self.image_path = image_path
        self.image = pygame.image.load(image_path)
        self.slot_rect = None  # Add this to store the rectangle


class Inventory:
    def __init__(self, max_slots=6):
        self.items = []
        self.max_slots = max_slots
        self.rows = 2
        self.cols = 3

    def add_item(self, item):
        if len(self.items) < self.max_slots:
            self.items.append(item)

    def remove_item(self, name):
        self.items = [item for item in self.items if item.name != name]

    def draw_inventory(self, surface, start_pos, area_size):
        slot_width = area_size[0] // self.cols
        slot_height = area_size[1] // self.rows

        for i in range(self.max_slots):
            row = i // self.cols
            col = i % self.cols
            x = start_pos[0] + col * slot_width
            y = start_pos[1] + row * slot_height
            slot_rect = pygame.Rect(x, y, slot_width, slot_height)

            if i < len(self.items):
                item = self.items[i]
                item_surface = pygame.transform.scale(item.image, (slot_width, slot_height))
                surface.blit(item_surface, slot_rect.topleft)
                item.slot_rect = slot_rect  # Update the item's rectangle each draw call
            else:
                pygame.draw.rect(surface, BG_COLOR, slot_rect)

            pygame.draw.rect(surface, BORDER_COLOR, slot_rect, 1)  # Draw slot border

    def get_item_at_pos(self, pos):
        for item in self.items:
            if item.slot_rect and item.slot_rect.collidepoint(pos):  # Check stored rectangle
                return item.name, item.description, item.image_path
        return None, None, None


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

    # Render and position the name directly under the image
    name_surface = font.render(name, True, TEXT_COLOR)
    name_rect = name_surface.get_rect(centerx=WIDTH // 2, top=image_rect.bottom + 10)
    surface.blit(name_surface, name_rect)

    # Initialize word wrapping for the description
    words = description.split(' ')
    space_width, line_height = font.size(' ')
    line_words = []
    line_width = 0

    # Create lines by accumulating words until the line width exceeds max_width
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

    # Draw the description text under the name
    text_top = name_rect.bottom + 10  # Start text below the name
    for line_words, line_width in lines:
        line_text = ' '.join(line_words)
        line_surface = font.render(line_text, True, TEXT_COLOR)
        line_rect = line_surface.get_rect(centerx=WIDTH // 2, top=text_top)
        text_top += line_height
        surface.blit(line_surface, line_rect)

    # Calculate overall card dimensions and position to ensure it is centered
    card_height = image_rect.height + (text_top - image_rect.top)
    card_top = max(0, HEIGHT // 2 - card_height // 2)
    card_rect = pygame.Rect((WIDTH - max_width) // 2, card_top, max_width, card_height)

    # Draw background and borders for the whole card
    pygame.draw.rect(surface, BORDER_COLOR, card_rect, 1)  # Drawing border

    # Blit the image within the card
    surface.blit(image, image_rect)



def main():
    global WIDTH, HEIGHT, screen
    game_engine = TextGameEngine()
    inventory_engine = InventoryEngine(game_engine.pipe, game_engine.image_pipe)
    start_items = inventory_engine.get_start_items()

    font_size = HEIGHT // 30
    font = get_font(font_size)
    input_text = ''
    base_y = HEIGHT - font_size * 2  # Position of the input area

    # Adjust the width and position calculations
    text_area_width = int(WIDTH * 0.68)
    image_area_width = WIDTH - text_area_width - 20

    image_position = (text_area_width + 10, 20)
    image_size = (image_area_width - 20, HEIGHT - 240)
    inventory_area_size = (image_area_width - 20, 200)
    inventory_position = (image_position[0], HEIGHT - inventory_area_size[1] - 20)


    running = True
    text_buffer = []
    image_path = None  # Path to the current image
    system_response, image = game_engine.generate_response()
    if image is not None:
        image.save('current.png', "PNG")
        image_path = 'current.png'
        show_image(screen, image_path, image_position, image_size)
    update_text_buffer(text_buffer, "> " + input_text, 8)
    update_text_buffer(text_buffer, system_response, 8)

    inventory = Inventory(6)


    # Add example inventory items for testing
    # inventory.add_item(InventoryItem("Example 1", "myapp.png"))
    # inventory.add_item(InventoryItem("Example 2", "myapp.png"))
    for item in start_items:
        inventory.add_item(InventoryItem(item['name'], item['description'], item['image']))
    while running:

        mouse_pos = pygame.mouse.get_pos()
        screen.fill(BG_COLOR)
        inventory.draw_inventory(screen, inventory_position, inventory_area_size)
        hovered_item_name, hovered_item_description, hovered_item_image = inventory.get_item_at_pos(mouse_pos)

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
                image_size = (image_area_width - 20, HEIGHT - 240)
                inventory_area_size = (image_area_width - 20, 200)
                inventory_position = (image_position[0], HEIGHT - inventory_area_size[1] - 20)

            elif event.type == KEYDOWN:
                if event.key == K_RETURN:
                    game_engine.add_user_message(input_text)
                    system_response, image = game_engine.generate_response()
                    if image is not None:
                        image.save('current.png', "PNG")
                        image_path = 'current.png'
                        show_image(screen, image_path, image_position, image_size)
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


        if hovered_item_name:
            draw_label(screen, hovered_item_name, hovered_item_description, font, mouse_pos, WIDTH / 3, hovered_item_image)  # Display name at mouse position

        y_offset = 20  # Top margin adjusted
        for text in text_buffer[-5:]:
            y_offset = draw_text(screen, text, (10, y_offset), TEXT_COLOR, font, text_area_width - 20)  # Left margin

        draw_text(screen, f"> {input_text}", (10, base_y), TEXT_COLOR, font, text_area_width - 20)  # Input field margin

        if image_path:
            show_image(screen, image_path, image_position, image_size)

        # Adjust border dimensions to fit within the window properly
        draw_bordered_box(screen, (10, 10, text_area_width, HEIGHT - 20), BORDER_COLOR, BORDER_WIDTH)
        draw_bordered_box(screen, (text_area_width + 10, 10, image_area_width - 20, HEIGHT - 20), BORDER_COLOR, BORDER_WIDTH)


        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
