"""
LLM Loader - Loads Qwen3 directly using HuggingFace transformers.
Model is loaded ONCE and cached. No separate server needed.
"""
import os
import re
import subprocess
import torch
import warnings

# Suppress HuggingFace max_new_tokens vs max_length warning spam
warnings.filterwarnings("ignore", message=".*max_new_tokens.*")
from transformers import logging as transformers_logging
transformers_logging.set_verbosity_error()

from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline as hf_pipeline
from langchain_huggingface import HuggingFacePipeline, ChatHuggingFace
from langchain_core.messages import BaseMessage

class RobustChatHuggingFace(ChatHuggingFace):
    """ChatHuggingFace subclass that:
    1. Removes the strict 'last message must be HumanMessage' validation.
    2. Supports enable_thinking=False for Qwen3 to suppress reasoning mode
       on structured/JSON extraction tasks (CA-IER).
    """
    enable_thinking: bool = True

    def _to_chat_prompt(self, messages: list[BaseMessage]) -> str:
        if not messages:
            raise ValueError("At least one message must be provided!")

        messages_dicts = []
        for m in messages:
            role = "user"
            class_name = m.__class__.__name__
            if "System" in class_name or getattr(m, "type", "") == "system":
                role = "system"
            elif "AI" in class_name or getattr(m, "type", "") == "ai" or getattr(m, "type", "") == "assistant":
                role = "assistant"
            elif "Human" in class_name or getattr(m, "type", "") == "human":
                role = "user"

            messages_dicts.append({"role": role, "content": m.content})

        # Use Qwen3's official enable_thinking parameter if supported
        try:
            return self.tokenizer.apply_chat_template(
                messages_dicts,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=self.enable_thinking,
            )
        except TypeError:
            # Fallback: tokenizer doesn't support enable_thinking
            return self.tokenizer.apply_chat_template(
                messages_dicts, tokenize=False, add_generation_prompt=True
            )

MODEL_NAME = os.environ.get("LLM_MODEL", "Qwen/Qwen3-14B")

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
    if hasattr(_model, "generation_config") and _model.generation_config is not None:
        _model.generation_config.max_length = None
    _model.eval()
    print(f"✅ Model {MODEL_NAME} berhasil dimuat!")
    return _model, _tokenizer


def strip_thinking(text: str) -> str:
    """Remove Qwen3 <think>...</think> reasoning blocks from output.
    Uses greedy match to handle long multi-line think blocks.
    Also handles unclosed <think> tags (model was cut off mid-think).
    """
    # Remove complete <think>...</think> blocks (greedy to handle long blocks)
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Also remove any unclosed <think> block (everything from <think> to end)
    cleaned = re.sub(r"<think>.*", "", cleaned, flags=re.DOTALL)
    cleaned = cleaned.strip()
    # Jika hasil pembersihan kosong, berarti seluruh teks adalah blok pemikiran (tidak ada jawaban)
    return cleaned if cleaned else ""


def get_chat_llm(temperature: float = 0.0, max_new_tokens: int = 512) -> RobustChatHuggingFace:
    """
    Returns a LangChain-compatible RobustChatHuggingFace using the cached Qwen3 model.
    Drop-in replacement for ChatOpenAI in all LangChain chains.
    Thinking mode OFF — suitable for NLG / conversational responses (prevents truncation).
    """
    model, tokenizer = load_model()
    do_sample = temperature > 0.0

    pipe = hf_pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=max_new_tokens,
        do_sample=do_sample,
        temperature=temperature if do_sample else 1.0,
        repetition_penalty=1.05,
        pad_token_id=tokenizer.eos_token_id,
        return_full_text=False,
    )

    return RobustChatHuggingFace(llm=HuggingFacePipeline(pipeline=pipe), enable_thinking=False)


def get_chat_llm_no_think(temperature: float = 0.0, max_new_tokens: int = 1024) -> RobustChatHuggingFace:
    """
    Like get_chat_llm() but with enable_thinking=False for Qwen3.
    Use for structured JSON extraction tasks (CA-IER) where reasoning tokens
    waste the token budget and increase latency significantly.
    """
    model, tokenizer = load_model()
    do_sample = temperature > 0.0

    pipe = hf_pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=max_new_tokens,
        do_sample=do_sample,
        temperature=temperature if do_sample else 1.0,
        repetition_penalty=1.05,
        pad_token_id=tokenizer.eos_token_id,
        return_full_text=False,
    )

    return RobustChatHuggingFace(llm=HuggingFacePipeline(pipeline=pipe), enable_thinking=False)
