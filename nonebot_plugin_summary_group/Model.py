from abc import abstractmethod

import httpx

from .Config import config


class Model:
    @abstractmethod
    async def summary_history(self, messages: list[dict[str, str]], prompt: str) -> str:
        pass


class Gemini(Model):
    def __init__(self, gemini_key: str, summary_model: str):
        self.gemini_key = gemini_key
        self.summary_model = summary_model

    async def summary_history(self, messages: list[dict[str, str]], prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.summary_model}:generateContent?key={self.gemini_key}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [
                {"parts": [{"text": prompt}], "role": "user"},
                {"parts": [{"text": str(messages)}], "role": "user"},
            ]
        }

        async with httpx.AsyncClient(
            proxy=config.proxy, timeout=config.time_out
        ) as client:
            try:
                response = await client.post(url, json=data, headers=headers)
                response.raise_for_status()

                result = response.json()

                return result["candidates"][0]["content"]["parts"][0]["text"]

            except httpx.TimeoutException:
                return "请求超时，请缩短总结消息数量或联系管理员调整超时时间"
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    return "API 调用次数已达上限，请稍后再试"
                return f"API请求失败 (HTTP {e.response.status_code})"
            except (httpx.RequestError, KeyError, ValueError) as e:
                return f"请求发生错误: {str(e)}"


class OpenAI(Model):
    def __init__(
        self,
        openai_base_url: str,
        openai_api_key: str,
        summary_model: str,
    ):
        self.openai_base_url = openai_base_url
        self.openai_api_key = openai_api_key
        self.summary_model = summary_model

    async def summary_history(self, messages: list[dict[str, str]], prompt: str) -> str:
        url = f"{self.openai_base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_api_key}",
        }
        data = {
            "model": self.summary_model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": str(messages)},
            ],
        }

        async with httpx.AsyncClient(
            proxy=config.proxy, timeout=config.time_out
        ) as client:
            try:
                response = await client.post(url, json=data, headers=headers)
                response.raise_for_status()

                result = response.json()

                return result["choices"][0]["message"]["content"]

            except httpx.TimeoutException:
                return "请求超时，请缩短总结消息数量或联系管理员调整超时时间"
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    return "API 调用次数已达上限，请稍后再试"
                return f"API请求失败 (HTTP {e.response.status_code})"
            except (httpx.RequestError, KeyError, ValueError) as e:
                return f"请求发生错误: {str(e)}"


def detect_model() -> Model:
    if config.gemini_key:
        return Gemini(config.gemini_key, config.summary_model)
    elif config.openai_base_url and config.openai_api_key:
        return OpenAI(
            config.openai_base_url, config.openai_api_key, config.summary_model
        )
    else:
        raise ValueError("未提供 Gemini API Key 或 OpenAI API Key。")
