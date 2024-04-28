import secrets

import torch
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
from diffusers import DiffusionPipeline, LCMScheduler, StableDiffusionXLPipeline
import os
os.makedirs('temp', exist_ok=True)
model_name="microsoft/Phi-3-mini-128k-instruct"
# Load the models and tokenizer
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="cuda",
    torch_dtype="auto",
    trust_remote_code=True,
)
tokenizer = AutoTokenizer.from_pretrained(model_name)
text_pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
)
# image_pipe = DiffusionPipeline.from_pretrained('PublicPrompts/All-In-One-Pixel-Model', use_safetensors=False,
#                                                     torch_dtype=torch.float16).to('cuda')

image_pipe = StableDiffusionXLPipeline.from_single_file('model.safetensors',
                                                    torch_dtype=torch.float16).to('cuda')
image_pipe.safety_checker = None
# set scheduler
image_pipe.scheduler = LCMScheduler.from_config(image_pipe.scheduler.config)

# load LCM-LoRA
image_pipe.load_lora_weights("latent-consistency/lcm-lora-sdxl")
image_pipe.fuse_lora()
def generate_text(prompt):
    # print(request_data)  # This will show what the server is actually receiving
    print(prompt)
    try:
        torch.manual_seed(secrets.randbelow(9999999999))
        generation_args = {
            "max_new_tokens": 2048,
            "return_full_text": False,
            "temperature": 0.75,
            "do_sample": True,
        }
        response = text_pipe(prompt, **generation_args)
        print(response[0]['generated_text'])
        return response[0]['generated_text']
    except Exception as e:
        print("LLM INFERENCE FAILED")
def generate_image(prompt):
    try:
        image = image_pipe(prompt=prompt, guidance_scale=1.0, num_inference_steps=7).images[0]
        image_path = f"temp/{hash(prompt)}.png"
        image.save(image_path, "PNG")
        return image_path
    except Exception as e:
        print("IMAGE INFERENCE FAILED")
