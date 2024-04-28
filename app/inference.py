import gc
import secrets

import torch
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
from diffusers import DiffusionPipeline, LCMScheduler, StableDiffusionXLPipeline, AutoPipelineForText2Image
import os
os.makedirs('temp', exist_ok=True)
model_name="microsoft/Phi-3-mini-128k-instruct"
# model_name="mistralai/Mistral-7B-Instruct-v0.2"
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

image_pipe = AutoPipelineForText2Image.from_pretrained('PublicPrompts/All-In-One-Pixel-Model',
                                                    torch_dtype=torch.float16).to('cuda')
image_pipe.safety_checker = None
# set scheduler
image_pipe.scheduler = LCMScheduler.from_config(image_pipe.scheduler.config)

# load LCM-LoRA
image_pipe.load_lora_weights("latent-consistency/lcm-lora-sdv1-5")
image_pipe.fuse_lora()


def optimize():
    global image_pipe
    try:
        from sfast.compilers.diffusion_pipeline_compiler import (
            compile,
            CompilationConfig,
        )

        image_pipe.config.force_upcast = False
        image_pipe.watermarker = None
        image_pipe.safety_checker = None
        image_pipe.set_progress_bar_config(disable=True)

        config = CompilationConfig.Default()
        config.enable_jit = True
        config.enable_jit_freeze = True
        config.enable_cuda_graph = True
        try:
            import triton
            config.enable_triton = True
        except:
            config.enable_triton = False

        config.enable_cnn_optimization = True
        config.preserve_parameters = False
        config.prefer_lowp_gemm = True
        config.enable_xformers = True
        config.channels_last = "channels_last"
        config.enable_fused_linear_geglu = True
        config.trace_scheduler = False

        # _ = self.__call__()
        # image_pipe.vae = torch.compile(image_pipe.vae, mode="reduce-overhead")

        image_pipe = compile(image_pipe, config)
    except:
        pass

@torch.inference_mode()
def generate_text(prompt):
    # try:
    torch.manual_seed(secrets.randbelow(9999999999))
    generation_args = {
        "max_new_tokens": 2048,
        "return_full_text": False,
        "temperature": 0.75,
        "do_sample": True,
    }
    response = text_pipe(prompt, **generation_args)
    return response[0]['generated_text']
    # except Exception as e:
    #     return "fail"
def cleanup():
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.ipc_collect()
@torch.inference_mode()
def generate_image(prompt):
    try:
        image = image_pipe(prompt=prompt, guidance_scale=1.0, num_inference_steps=7).images[0]
        image_path = f"temp/{hash(prompt)}.png"
        image.save(image_path, "PNG")
        cleanup()
        return image_path
    except Exception as e:
        print("IMAGE INFERENCE FAILED")

def count_tokens(prompts):
    # Check token count before adding new user message
    summed = 0
    for i in [tokenizer.encode(message['content']) for message in prompts]:
        summed += len(i)
    return summed