# 注册不同的Engine
#
# Keep the OpenAI-compatible engine mandatory, and load vendor/local-model
# engines only when their optional dependencies or source files are available.
# This lets the DeepSeek/OpenAI path run without installing heavyweight local
# model packages such as torch/transformers.
from .base_engine import Engine
from .gpt import GPTEngine
from .chatglm import ChatGLMEngine
from .minimax import MiniMaxEngine
from .wenxin import WenXinEngine

try:
    from .qwen import QwenEngine
except ImportError:
    QwenEngine = None

try:
    from .huatuogpt import HuatuoGPTEngine
except ImportError:
    HuatuoGPTEngine = None

try:
    from .hf import HFEngine
except ImportError:
    HFEngine = None


__all__ = [
    "Engine",
    "GPTEngine",
    "ChatGLMEngine",
    "MiniMaxEngine",
    "WenXinEngine",
]

if QwenEngine is not None:
    __all__.append("QwenEngine")
if HuatuoGPTEngine is not None:
    __all__.append("HuatuoGPTEngine")
if HFEngine is not None:
    __all__.append("HFEngine")
