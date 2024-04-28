import pygame
import sys

from pygame.locals import *
from llm import TextGameEngine, InventoryEngine, InventoryItem

# Constants
FPS = 30
BG_COLOR = pygame.Color('black')
TEXT_COLOR = pygame.Color('white')
USER_TEXT_COLOR = pygame.Color('green')

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
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime



def add_to_pdf(c, text, image_path, ypos):
    """ Adds word-wrapped text and an image to the PDF next to the text box. """
    c.setFont("Helvetica", 12)
    max_text_width = 300  # Width of the text box for wrapping

    # Prepare the text object for adding text
    text_object = c.beginText(40, ypos)

    # Word wrapping
    words = text.split()
    line = []
    for word in words:
        # Check the width of the line with the new word added
        test_line = ' '.join(line + [word])
        if c.stringWidth(test_line, "Helvetica", 12) < max_text_width:
            line.append(word)
        else:
            # If the line is too wide, add the current line and start a new one
            text_object.textLine(' '.join(line))
            line = [word]

    # Add the last line
    if line:
        text_object.textLine(' '.join(line))

    # Draw the text object on the canvas
    c.drawText(text_object)

    # Current Y position after text has been added
    current_ypos = text_object.getY()

    # Calculate the height used by the text
    text_height = ypos - current_ypos + 15  # Adding some padding for spacing

    # Load and draw the image next to the text box if the path is valid
    if image_path:
        try:
            from PIL import Image
            im = Image.open(image_path)
            im_width, im_height = im.size
            aspect_ratio = im_width / im_height
            image_height = 75  # Set a fixed image height
            image_width = int(image_height * aspect_ratio)  # Calculate width based on aspect ratio

            # Ensure the image starts at the same vertical position as the text began
            c.drawImage(image_path, 350, ypos - image_height, width=image_width, height=image_height, preserveAspectRatio=True)
        except Exception as e:
            print(f"Failed to load image for PDF: {e}")

    # Move ypos for the next content, adjust spacing considering the text height
    return current_ypos - 15  # Adjust ypos downwards for next content, adding padding




def create_pdf_log():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"game_log_{timestamp}.pdf"
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    c.setTitle(f"Game Session Log - {timestamp}")
    return c, width, height


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
def draw_text_area(surface, text, position, color, font, wrap_width):
    """Modified to return the bottom y-coordinate after drawing."""
    words = text.split()
    space_width, line_height = font.size(" ")
    x, start_y = position
    y = start_y

    for word in words:
        word_surface = font.render(word, True, color)
        word_width, word_height = word_surface.get_size()

        if x + word_width >= wrap_width:
            x = position[0]  # Reset to start of line
            y += line_height  # Move down to next line

        surface.blit(word_surface, (x, y))
        x += word_width + space_width

    return y + line_height

def draw_user_input_box(surface, input_text, position, area_width, area_height, font, color, border_color):
    input_box_rect = pygame.Rect(position[0], position[1], area_width, area_height)
    pygame.draw.rect(surface, BG_COLOR, input_box_rect)  # Fill background
    pygame.draw.rect(surface, border_color, input_box_rect, BORDER_WIDTH)  # Draw border

    # Draw user input text inside the box
    text_x = position[0] + 15  # A small padding from the border
    text_y = position[1] + 10
    draw_text_area(surface, f"> {input_text}", (text_x, text_y), USER_TEXT_COLOR, font, position[0] + area_width - 10)

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

def render_screen(input_text, screen, text_buffer, font, base_y, text_area_width, inventory_engine, inventory_position, inventory_area_size, score, score_position, image_area_width, image_path, image_position, image_size):
    # Clear the screen
    screen.fill(BG_COLOR)

    # Draw inventory
    inventory_engine.draw_inventory(screen, inventory_position, inventory_area_size)

    # Draw text buffer
    y_offset = 20
    for text in text_buffer[-5:]:  # Display last 5 messages
        y_offset = draw_text(screen, text, (10, y_offset), TEXT_COLOR, font, text_area_width - 20)
    if input_text is not None:
        # Draw input prompt
        draw_text(screen, f"> {input_text}", (10, base_y), USER_TEXT_COLOR, font, text_area_width - 20)

    # Show image if available
    if image_path:
        show_image(screen, image_path, image_position, image_size)

    # Draw the score
    draw_score(screen, score, score_position, TEXT_COLOR, font, image_area_width)

    # Draw borders
    draw_bordered_box(screen, (10, 10, text_area_width, HEIGHT - 20), BORDER_COLOR, BORDER_WIDTH)
    draw_bordered_box(screen, (text_area_width + 10, 10, image_area_width - 20, HEIGHT - 20), BORDER_COLOR, BORDER_WIDTH)

    # Update the display
    pygame.display.flip()
def main():
    global WIDTH, HEIGHT, screen
    game_engine = TextGameEngine()
    inventory_engine = InventoryEngine(game_engine.api_comms, 6)
    # inventory = Inventory(6)
    game_engine.inventory_engine = inventory_engine
    # inventory_engine.inventory = inventory
    start_items = inventory_engine.get_start_items()
    system_response = ""
    pdf_input = ""
    font_size = HEIGHT // 35
    font = get_font(font_size)
    input_text = ''
    base_y = HEIGHT - font_size * 3  # Adjust base_y to be above the bottom
    pdf, pdf_width, pdf_height = create_pdf_log()
    ypos = pdf_height - 40  # Start close to the top of the page

    # Adjust the width and position calculations
    # Adjust text area size and positions
    text_area_width = int(WIDTH * 0.68)
    text_area_height = HEIGHT - font_size * 3 - 20  # Subtract height of input box and some margin
    input_area_height = font_size * 3  # Enough for two lines of text
    image_area_width = WIDTH - text_area_width - 20
    score_position = (text_area_width + text_area_width // 2, 10)  # Starting x position of the image area, y position remains at the top
    score = 0
    image_position = (text_area_width + 10, 20)
    image_size = (image_area_width - 20, HEIGHT - 240)
    inventory_area_size = (image_area_width - 20, 200)
    inventory_position = (image_position[0], HEIGHT - inventory_area_size[1] - 20)
    user_input = ""

    running = True
    text_buffer = []
    image_path = None  # Path to the current image
    #system_response, image_path, _ = game_engine.generate_response()
    if image_path is not None:
        show_image(screen, image_path, image_position, image_size)
    update_text_buffer(text_buffer, "> " + input_text, 8)

    for item in start_items:
        inventory_engine.add_item(InventoryItem(item['name'], item['description'], item['image']))

    # Set up timer for self-play
    last_interaction_time = pygame.time.get_ticks()
    inactivity_threshold = 1500  # 5 seconds
    while running:
        current_time = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(BG_COLOR)

        y_offset = 25  # Adjust top margin
        for text in text_buffer[-5:]:  # Display last 5 messages
            y_offset = draw_text_area(screen, text, (25, y_offset), TEXT_COLOR, font, text_area_width - 20)
        draw_user_input_box(screen, input_text, (10, HEIGHT - input_area_height - 10), text_area_width, input_area_height, font, TEXT_COLOR, BORDER_COLOR)

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
                score_position = (text_area_width + text_area_width // 2,
                                  10)  # Starting x position of the image area, y position remains at the top

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

        if (current_time - last_interaction_time) > inactivity_threshold:
            user_input = game_engine.self_play()
            update_text_buffer(text_buffer, "> " + user_input, 8)
            #render_screen(None, screen, text_buffer, font, base_y, text_area_width, inventory_engine, inventory_position, inventory_area_size, score, score_position, image_area_width, image_path, image_position, image_size)
            game_engine.add_user_message(user_input)
            system_response, image_path, new_score = game_engine.generate_response()
            if system_response is not None:
                update_text_buffer(text_buffer, system_response, 8)
                if new_score is not None:
                    score += new_score
                last_interaction_time = pygame.time.get_ticks()  # Reset the timer after self_play

        current_input = f"User Input: {user_input}\nSystem Response: {system_response}"
        if pdf_input != current_input:
            pdf_input = current_input
            ypos = add_to_pdf(pdf, pdf_input, image_path, ypos)
            if ypos < 100:  # Check to avoid writing too close to the bottom
                pdf.showPage()
                ypos = pdf_height - 40
        draw_score(screen, score, score_position, TEXT_COLOR, font, image_area_width)

        # y_offset = 20  # Top margin adjusted
        # for text in text_buffer[-5:]:
        #     y_offset = draw_text(screen, text, (10, y_offset), TEXT_COLOR, font, text_area_width - 20)  # Left margin

        #draw_text(screen, f"> {input_text}", (10, base_y), TEXT_COLOR, font, text_area_width - 20)  # Input field margin

        if image_path:
            show_image(screen, image_path, image_position, image_size)

        # Adjust border dimensions to fit within the window properly
        draw_bordered_box(screen, (10, 10, text_area_width, HEIGHT - 20), BORDER_COLOR, BORDER_WIDTH)
        draw_bordered_box(screen, (text_area_width + 10, 10, image_area_width - 20, HEIGHT - 20), BORDER_COLOR, BORDER_WIDTH)
        if hovered_item_name:
            draw_label(screen, hovered_item_name, hovered_item_description, font, mouse_pos, WIDTH / 3, hovered_item_image)  # Display name at mouse position

        pygame.display.flip()
        clock.tick(FPS)

    # Save the PDF before quitting
    pdf.save()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
