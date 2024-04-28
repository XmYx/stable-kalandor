import ast
import gc
import json
import re
import secrets

import pygame
import torch
import os

# Define the cache directory path
cache_dir = os.path.expanduser('~/kalandor/hf_cache')

# Set the environment variable for HuggingFace cache
# os.environ['HF_HOME'] = cache_dir

# Create the directory if it doesn't exist
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

print(f"HuggingFace cache directory is set to: {cache_dir}")
reminder = 'I will always answer in the format: {"image":"Description", "answer":"Your Text Answer"}'
BG_COLOR = pygame.Color('black')
TEXT_COLOR = pygame.Color('white')
BORDER_COLOR = pygame.Color('gray')
from inference import generate_image, generate_text, count_tokens


def cleanup():
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.ipc_collect()
class APICommunication:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def generate_text(self, prompt, max_tokens, summary={'role':'user', 'content':'Summary of previous events'}):
        """Generates text based on the prompt, retrying until a successful response is obtained."""
        response = None
        while response is None or response == 'fail':
            token_sum = count_tokens(prompt)

            if token_sum > 126000:
                prompt = [prompt[0], summary, prompt[-1]]

            response = generate_text(prompt)  # Assuming generate_text is a callable that returns the response
            if response == 'fail':
                print("Failed to generate text, retrying...")
            cleanup()  # Ensure resources are cleaned or reset between retries
        return response

    def generate_image(self, prompt):
        response = generate_image(prompt)
        cleanup()
        return response

class InventoryItem:
    def __init__(self, name, description, image_path):
        self.name = name
        self.description = description
        self.image_path = image_path
        self.image = pygame.image.load(image_path)
        self.slot_rect = None  # Add this to store the rectangle
class InventoryEngine:

    def __init__(self, api, max_slots):
        self.items = []
        self.api = api
        self.inventory = None
        self.max_slots = max_slots
        self.rows = 2
        self.cols = 3

    def add_item(self, item):
        if len(self.items) < self.max_slots:
            self.items.append(item)

    def remove_item(self, name):
        self.items = [item for item in self.items if item.name.lower() != name.lower()]
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

    def generate_single_item(self, item):
        # Create a message prompting the generation of a single item
        messages = [
            {'role': 'system',
             'content': 'I am a role playing game inventory generator AGI, and your task is to generate a single item.'
                        f'I will provide the item name and description in the format:'
                        '{"name": "Item Name", "description": "Item Description"}.'},
            {'role': 'user',
             'content':f'You must provide the name and description for the item {item}'
                        ' You must answer in the format: {"name": "Item Name", "description": "Item Description"}'}
        ]
        response = self.generate_response(messages)
        try:
            # Parse the response from the language model
            item_data = ast.literal_eval(response)
            item_name = item_data['name']
            item_description = item_data['description']
            filename = self.generate_image('pixel art, ' + item_description)
            return InventoryItem(item_name, item_description, filename)
        except SyntaxError as e:
            print(f"Error parsing LLM response: {str(e)}")
            print(f"LLM response was: {response}")
            return None

    def get_start_items(self):

        messages = [
            {'role': 'system',
             'content': f'I am a role playing game inventory generator AGI, and your first task is to fill a {self.max_slots} slot inventory with objects.'
                        ' I must answer in the following format: [{"name":"Item Name", "description":"Item Description"}, ...]'},
            {'role': 'user',
             'content': f'Generate the starting list of objects'},
        ]
        starting_items = self.generate_response(messages)
        starting_items = ast.literal_eval(starting_items)
        counter = 0
        for i in starting_items:
            filename = self.generate_image(i.get('description', 'game inventory item'))
            i['image'] = filename
            counter += 1
        return starting_items

    def use_item(self, item, action):

        if isinstance(item, list):
            for i in item:
                self.use_item(i.lower(), action)
        else:

            normalized_item = item.lower()  # Normalize item to lower case
            # Find item in the inventory, case-insensitively
            if any(stored_item.name.lower() == normalized_item for stored_item in self.items):
                try:
                    messages = [
                        {'role': 'system',
                         'content': f'I am a role playing game inventory AGI, and my task is to make use of the item and scenario presented by the user.'
                                    ' I must decide the actions consequence, and the items fate from the following choices: no_action, remove_item'
                                    },
                        {'role': 'user',
                         'content': f'Lets use {normalized_item} for: {action}, what happens to the item,'
                                    ' You must answer in the format: {"effect": "description of what happens", "keep_item": true or false}'}
                    ]
                    result = self.generate_response(messages)
                    try:
                        parsed_response = ast.literal_eval(result)
                        effect = parsed_response['effect']
                        keep_item = parsed_response['keep_item']

                        print(f"Effect of using {normalized_item}: {effect}")
                        if not keep_item:
                            self.remove_item(normalized_item)  # Remove using normalized name
                        else:
                            print(f"{normalized_item} remains in the inventory after use.")

                    except SyntaxError as e:
                        print(f"Error parsing LLM response: {str(e)}")
                        print(f"LLM response was: {result}")
                except:
                    pass
    def get_current_items(self):
        return [i.name for i in self.items]
    def generate_response(self, messages):
        output = self.api.generate_text(messages, 1024)
        return output
    def generate_image(self, prompt):
        return self.api.generate_image(prompt)
def extract_with_nested_braces(text):
    stack = 0
    start = -1
    for index, char in enumerate(text):
        if char == '{':
            if stack == 0:
                start = index
            stack += 1
        elif char == '}':
            stack -= 1
            if stack == 0 and start != -1:
                return text[start:index+1]
    return None
class TextGameEngine:
    def __init__(self, max_tokens=128000):
        self.max_tokens = max_tokens
        self.messages = [
        ]
        self.api_comms = APICommunication()
        self.inventory_engine = None
        self.location = ""
        self.summary = ""
        self.reminder = ('Adhere to the established game environment, location, and narrative. '
                         'Choose an action for inventory items: no_action, use_inventory_item, add_to_inventory, remove_from_inventory. '
                         'On request, list the actual inventory. Your "answer" must be immersive, like a role playing game master.'
                         'Respond with the next scenario formatted as: {"image":"Image Description", "answer":"Adventure content and next question", "score":-10-10, "action":"choose from above", "item":"[no_items or item names]", "location":"Current Location"}')
        self.alter_system_message()
    def alter_system_message(self, location='Unknown', inventory='Empty', summary="None"):
        # Update class attributes to reflect current game state
        self.location = location
        self.summary = summary

        # Update the system message to reflect current game state
        content = (
            f'I am a sentient AGI Role Playing assistant tasked with maintaining a consistent game environment and narrative flow. '
            f'I will score user actions based on their relevance and effectiveness within the current environment. '
            f'I ensure that all interactions with objects are realistic and adhere to the environment. '
            f'Choices regarding the usage of inventory items must be context-sensitive, ensuring no random environment shifts unless narratively justified. '
            f'The current location is {location}, your inventory contains: {inventory}, the current situation is: {summary}. '
            'I will always provide an action choice from: no_action, use_inventory_item, add_to_inventory, remove_from_inventory. '
            'I must respond with the next scenario formatted as: {"image":"portrait of a sorcerer, highly detailed, photorealistic", "answer":"Adventure content and next question", "score":-10-10, "action":"no_action", "item":"[no_items]", "location":"Current Location"}')

        if not self.messages:
            self.messages.append({'role': 'system', 'content': content})
        else:
            self.messages[0] = {'role': 'system', 'content': content}
        self.initial_message = self.messages[0]

    def self_play(self):
        """Generate user input based on previous events and the current scenario."""
        # Fetch the current scenario as context
        current_scenario = self.messages[-1]['content'] if self.messages else 'no scenario known yet'

        # Generate a plausible user action based on the current context
        synthetic_user_input = [{
            'role': 'system',
            'content': f'I am a role playing AGI, and will take action based on the input'
                        'I will always answer with a single string emulating user input reacting to situations '
                       'in a role playing game.'
        },
        {
            'role': 'user',
            'content': f'Generate plausible action based on the scenario: {current_scenario}'
                        ' You must answer with a single string emualating the next user input.'
        }]

        response = self.api_comms.generate_text(synthetic_user_input, 1024)
        #
        print(response)
        # parsed = ast.literal_eval(response)


        return response
        # Append generated user action as user message
        self.add_user_message(response)
        # Proceed to generate the system's response to the synthetic user input
        return self.generate_response()
    def generate_response(self):
        try:
            self.messages[-1]['content'] = self.messages[-1]['content'] + f" We are currently in {self.location} and our inventory contains: {self.inventory_engine.get_current_items()} " + self.reminder
            generated_text = self.api_comms.generate_text(self.messages, 1024, summary={'role':'user', 'content':self.summary})

            if count_tokens(self.messages) > 126000:
                self.reset_conversation(self.summary)

            print(generated_text)
            self.messages.append({'role': 'system', 'content': generated_text})
            parsed = ast.literal_eval(generated_text)
            action = parsed.get('action', 'no_action')
            item = parsed.get('item', 'no_item')
            score = int(parsed.get('score', 0))
            if action:
                self.handle_inventory_action(action, item)
            image = self.api_comms.generate_image(prompt=parsed['image'])


            answer = parsed.get('answer', parsed['image'])
            self.location = parsed.get('location', self.location)
            self.alter_system_message(self.location, self.inventory_engine.get_current_items(), self.summary)
            return answer, image, score
        except Exception as e:
            print(repr(e))
            return None, None, None

    def handle_inventory_action(self, action, item_name):
        if action == 'add_to_inventory':
            new_item = self.inventory_engine.generate_single_item(item_name)
            if new_item:
                self.inventory_engine.add_item(new_item)
        elif action == 'remove_from_inventory':
            self.inventory_engine.remove_item(item_name)
        elif action == 'use_inventory_item':
            summary = self.summarize_conversation()
            self.inventory_engine.use_item(item_name, summary)
    def add_user_message(self, user_message):
        self.messages.append({'role': 'user', 'content': user_message})
    def generate_item_image(self, prompt):
        return self.api_comms.generate_image(prompt)
    def summarize_conversation(self):
        #self.messages.append({'role': 'user', 'content': 'As the engine can not handle any more information, summarize everything that happened so far, and is relevant for the storyline in a single message that we will store for the future.'})

        sums = self.messages.copy()
        sums.append({'role': 'user', 'content': 'Your task is now to conclude the previous happenings in the following format: {"summary":"Summary of all previous events", "location":"Current Location"}'})
        self.summary = self.api_comms.generate_text(sums, 1024)
        print("Summary:", self.summary)
        return self.summary
    def reset_conversation(self, summarized_text):
        print("RESET")
        self.messages = [
            self.initial_message,
            {'role': 'user', 'content': f'Here is a summary of everything that happened so far: {summarized_text}'},
            {'role': 'system', 'content': 'Thank you. I am awaiting input to continue your adventure'},
        ]