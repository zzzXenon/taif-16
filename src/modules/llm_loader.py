"""
LLM Loader - Loads Qwen3 directly using HuggingFace transformers.
Model is loaded ONCE and cached. No separate server needed.
"""
import os
import re
import subprocess
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline as hf_pipeline, GenerationConfig
from langchain_huggingface import HuggingFacePipeline, ChatHuggingFace

MODEL_NAME = "Qwen/Qwen3-8B"

_model = None
_tokenizer = None


def get_free_gpu() -> str:
    """Returns the index of the GPU with the most free VRAM."""
    try:
        result = subprocess.check_output(
            "nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits",
            shell=True
        ).decode("utf-8")
        gpu_info = []
        for line in result.strip().split("\n"):
            parts = line.split(",")
            gpu_info.append((int(parts[0].strip()), int(parts[1].strip())))
        gpu_info.sort(key=lambda x: x[1])
        return str(gpu_info[0][0])
    except Exception:
        return "0"


def load_model():
    """Load Qwen3 model and tokenizer once, cache for all subsequent calls."""
    global _model, _tokenizer
    if _model is not None:
        return _model, _tokenizer

    if torch.cuda.is_available():
        gpu_id = get_free_gpu()
        os.environ["CUDA_VISIBLE_DEVICES"] = gpu_id
        print(f"✅ Menggunakan GPU {gpu_id}")
    else:
        print("⚠️ GPU tidak tersedia, menggunakan CPU")

    print(f"🚀 Memuat tokenizer {MODEL_NAME}...")
    _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    print(f"🚀 Memuat model {MODEL_NAME} (device_map=auto)...")
    _model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        dtype=torch.float16,
        device_map="auto"
    )
    _model.eval()
    print(f"✅ Model {MODEL_NAME} berhasil dimuat!")
    return _model, _tokenizer


def strip_thinking(text: str) -> str:
    """Remove Qwen3 <think>...</think> reasoning blocks from output."""
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    return cleaned if cleaned else text


def get_chat_llm(temperature: float = 0.0, max_new_tokens: int = 512) -> ChatHuggingFace:
    """
    Returns a LangChain-compatible ChatHuggingFace using the cached Qwen3 model.
    Drop-in replacement for ChatOpenAI in all LangChain chains.
    """
    model, tokenizer = load_model()
    do_sample = temperature > 0.0

    gen_config = GenerationConfig(
        max_new_tokens=max_new_tokens,
        do_sample=do_sample,
        temperature=temperature if do_sample else 1.0,
        repetition_penalty=1.05,
        pad_token_id=tokenizer.eos_token_id,
    )

    pipe = hf_pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        generation_config=gen_config,
        return_full_text=False,
    )

    return ChatHuggingFace(llm=HuggingFacePipeline(pipeline=pipe))
