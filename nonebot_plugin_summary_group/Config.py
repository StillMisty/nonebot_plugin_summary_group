from nonebot import get_plugin_config
from pydantic import BaseModel


class Config(BaseModel):
    gemini_key: str | None = None  # gemini接口密钥
    openai_base_url: str | None = None  # openai接口地址
    openai_api_key: str | None = None  # openai接口密钥
    summary_model: str = "gemini-1.5-flash"  # 模型名称
    proxy: str | None = None  # 代理设置
    summary_max_length: int = 2000  # 总结最大长度
    summary_min_length: int = 50  # 总结最小长度
    summary_cool_down: int = 0  # 总结冷却时间（0即无冷却，针对人，而非群）


config = get_plugin_config(Config)
