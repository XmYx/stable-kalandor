import ast
import json
import re
import secrets

import torch
from diffusers import DiffusionPipeline, LCMScheduler
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import os

# Define the cache directory path
cache_dir = os.path.expanduser('~/kalandor/hf_cache')

# Set the environment variable for HuggingFace cache
os.environ['HF_HOME'] = cache_dir

# Create the directory if it doesn't exist
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

print(f"HuggingFace cache directory is set to: {cache_dir}")
# torch.random.manual_seed(0)
#
# model = AutoModelForCausalLM.from_pretrained(
#     "microsoft/Phi-3-mini-128k-instruct",
#     device_map="cuda",
#     torch_dtype="auto",
#     trust_remote_code=True,
# )
# tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3-mini-128k-instruct")
#
#
# game_start_messages = [
#     {"role": "system", "content": "You are a gore role playing game engine. In this cyberpunk world, you will ask questions from the user, and evaluate their responses"},
#     {"role": "user", "content": "Let the game begin"}
# ]
#
# pipe = pipeline(
#     "text-generation",
#     model=model,
#     tokenizer=tokenizer,
# )
#
# generation_args = {
#     "max_new_tokens": 500,
#     "return_full_text": False,
#     "temperature": 0.0,
#     "do_sample": False,
# }
#
# output = pipe(game_start_messages, **generation_args)
# print(output[0]['generated_text'])
reminder = 'Always answer in the format: {"image":"Description", "answer":"Your Text Answer"}'

class InventoryEngine:

    def __init__(self, llm_pipe, image_pipe):
        self.items = []
        self.max_slots = 6
        self.llm_pipe = llm_pipe
        self.image_pipe = image_pipe

    def add_item(self, item):
        if item not in self.items and len(self.items) < self.max_slots + 1:
            self.items.append(item)

    def get_start_items(self):

        messages = [
            {'role': 'system',
             'content': f'You are a role playing game inventory generator AGI, and your first task is to fill a {self.max_slots} slot inventory with objects.'
                        ' You must answer in the following format: [{"name":"Item Name", "description":"Item Description"}, ...]'},
            {'role': 'user',
             'content': f'Generate the starting list of objects'},
        ]
        starting_items = self.generate_response(messages)
        starting_items = ast.literal_eval(starting_items)
        counter = 0
        for i in starting_items:
            image = self.image_pipe(prompt='pixel art, ' + i.get('description', 'indie game inventory item'),
                                    guidance_scale=1.0,
                                    num_inference_steps=7).images[0]
            filename = f'item_{counter}.png'
            image.save(filename, "PNG")
            i['image'] = filename
            counter += 1
        return starting_items

    def take_action(self, item, action):
        messages = [
            {'role': 'system',
             'content': f'You are a role playing game inventory AGI, and your task is to make use of the item and scenario presented by the user.'
                        'You must decide the actions consequence, and the items faith from the following choices: no_action, remove_item'
                        'You must answer in the following format: {"name":"Item Name", "consequence":"The actions consequence", "faith":"no_action"}'},
            {'role': 'user',
             'content': f'Lets use {item} to {action}'}
        ]
        result = self.generate_response(messages)
        print(result)
    def generate_response(self, messages):
        torch.random.manual_seed(secrets.randbelow(999999999999))

        generation_args = {
            "max_new_tokens": 500,
            "return_full_text": False,
            "temperature": 0.0,
            "do_sample": False,
        }
        output = self.llm_pipe(messages, **generation_args)
        generated_text = output[0]['generated_text']
        return generated_text

class TextGameEngine:
    def __init__(self, model_name="microsoft/Phi-3-mini-128k-instruct", max_tokens=4096):
        self.max_tokens = max_tokens
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="cuda",
            torch_dtype="auto",
            trust_remote_code=True,
        )
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
        )
        self.messages = [
            {'role': 'system', 'content': 'You are a gore role playing game engine. Your task is to generate image prompts and be the role play game providing text answers as well.'
                                          'In world, you will continously generate an adventure, sometimes surprising, sometimes limiting the player, '
                                          'but never allowing impossible feats, and always make a mood image Description, '
                                          'and ask the user for a decision in your Answer, and evaluate their responses. '
                                          'You must score the users actions.'
                                          'You must also choose from one of the following actions: no_action, use_inventory_item, add_to_inventory, remove_from_inventory'
                                          'Always answer in the format: {"image":"portrait of a sorcerer, pixel art, detailed", "answer":"Adventure content", "score":0-10, "action":"no_action", "item":"no_item"}'},
            {'role': 'user', 'content': 'Generate a random adventure, and lets do an in medias res start, throughout the game, do not allow impossible choices, or immature ending:'}
        ]
        self.initial_message = self.messages[0]

        self.image_pipe = DiffusionPipeline.from_pretrained('PublicPrompts/All-In-One-Pixel-Model', use_safetensors=False, torch_dtype=torch.float16).to('cuda')
        self.image_pipe.safety_checker = None
        # set scheduler
        self.image_pipe.scheduler = LCMScheduler.from_config(self.image_pipe.scheduler.config)

        # load LCM-LoRA
        self.image_pipe.load_lora_weights("latent-consistency/lcm-lora-sdv1-5")

    def generate_response(self):
        torch.random.manual_seed(secrets.randbelow(999999999999))

        generation_args = {
            "max_new_tokens": 500,
            "return_full_text": False,
            "temperature": 0.0,
            "do_sample": False,
        }
        output = self.pipe(self.messages, **generation_args)
        generated_text = output[0]['generated_text']
        self.messages.append({'role': 'system', 'content': generated_text})

        # parsed_response = json.loads(generated_text.replace("'", '"'))

        try:
            match = re.search(r'\{(.+?)\}', generated_text)
            if match:
                content_within_braces = match.group(1)
                parsed = ast.literal_eval('{' + content_within_braces + '}')
            else:
                parsed = {"image":generated_text}
            # parsed = ast.literal_eval(generated_text)
            print("PARSED", parsed)
            image = self.image_pipe(prompt=parsed['image'],
                                    guidance_scale=1.0,
                                    num_inference_steps=7).images[0]
            answer = parsed.get('answer', parsed['image'])
            return answer, image

        except:
            return generated_text, None


    def add_user_message(self, user_message):
        # Check token count before adding new user message
        summed = 0
        for i in [self.tokenizer.encode(message['content']) for message in self.messages]:
            summed += len(i)
        # current_tokens = sum(self.tokenizer.encode(message['content']) for message in self.messages)
        message_tokens = len(self.tokenizer.encode(user_message))
        if summed + message_tokens >= self.max_tokens:
            # Summarize and reset
            summarized_text = self.summarize_conversation()
            self.reset_conversation(summarized_text)
        # else:
        self.messages.append({'role': 'user', 'content': user_message})

    def summarize_conversation(self):
        #conversation_text = ' '.join(message['content'] for message in self.messages)
        summary_args = {
            'max_new_tokens': 1024,
            'return_full_text': False,
            'temperature': 0.5,
            'do_sample': True,
            'top_k': 50
        }
        self.messages.append({'role': 'user', 'content': 'As the engine can not handle any more information, summarize everything that happened so far, and is relevant for the storyline in a single message that we will store for the future.'})
        summary = self.pipe(self.messages, **summary_args)
        print("Summary:", summary)
        return summary[0]['generated_text']

    def reset_conversation(self, summarized_text):
        print("RESET")
        self.messages = [
            self.initial_message,
            {'role': 'user', 'content': f'Here is a summary of everything that happened so far: {summarized_text}'},
            {'role': 'system', 'content': 'Thank you. I am awaiting input to continue your adventure'},
        ]