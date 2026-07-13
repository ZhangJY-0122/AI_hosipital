import os
import openai
from openai import OpenAI
from utils.register import register_class
from .base_engine import Engine
import time


@register_class(alias="Engine.GPT")
class GPTEngine(Engine):
    def __init__(self, openai_api_key, openai_api_base=None, openai_model_name=None, temperature=0.0, max_tokens=1024, top_p=1, frequency_penalty=0, presence_penalty=0):
        openai_api_key = openai_api_key if openai_api_key is not None else os.environ.get('OPENAI_API_KEY')
        if openai_api_key is None:
            raise RuntimeError(
                "OPENAI_API_KEY is required. For DeepSeek, set OPENAI_API_KEY "
                "to your DeepSeek API key and OPENAI_API_BASE to "
                "https://api.deepseek.com/v1."
            )
        openai_api_base = openai_api_base if openai_api_base is not None else os.environ.get('OPENAI_API_BASE')

        self.model_name = openai_model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty

        if openai_api_base is not None:
            self.client = OpenAI(
                api_key=openai_api_key,
                base_url=openai_api_base
            )
        else:
            self.client = OpenAI(
                api_key=openai_api_key,
            )

    def get_response(self, messages):
        model_name = self.model_name
        i = 0
        response = None
        last_error = None
        while i < 5:
            try:
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    top_p=self.top_p,
                    frequency_penalty=self.frequency_penalty,
                    presence_penalty=self.presence_penalty
                )
                break
            except openai.BadRequestError as e:
                last_error = e
                print(f"OpenAI bad request for model {model_name}: {e}")
                if model_name == "gpt-3.5-turbo":
                    model_name = "gpt-3.5-turbo-16k"
                i += 1
            except openai.RateLimitError as e:
                last_error = e
                print(f"OpenAI rate limit for model {model_name}: {e}")
                time.sleep(10)
                i += 1
            except Exception as e:
                last_error = e
                print(f"OpenAI request failed for model {model_name}: {type(e).__name__}: {e}")
                i += 1
                time.sleep(5)
                continue
            # else:
            #     i += 1
        if response is None:
            raise RuntimeError(f"OpenAI request failed after 5 attempts for model {model_name}") from last_error
        return response.choices[0].message.content
