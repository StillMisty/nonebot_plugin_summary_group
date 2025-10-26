from typing import Annotated, Any, Literal, Union

from nonebot import get_plugin_config
from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


class BaseProviderConfig(BaseModel):
    """所有AI服务商账户共有的基础配置"""

    nickname: str = Field(description="账户的唯一别名，用于在指令中指定账户")
    api_key: str = Field(description="该账户的 API Key")
    model: str = Field(description="该账户要使用的模型名称")
    proxy: str | None = Field(None, description="为该账户单独设置代理")
    time_out: int = Field(60, description="该账户的 API 请求超时时间(秒)")


class OpenAIConfig(BaseProviderConfig):
    """OpenAI 账户特定配置"""

    provider: Literal["openai"] = "openai"
    base_url: HttpUrl = Field(
        description="OpenAI API 兼容格式的访问地址",
    )


class GeminiConfig(BaseProviderConfig):
    """Gemini 账户特定配置"""

    provider: Literal["gemini"] = "gemini"


AIProviderConfig = Annotated[
    Union[OpenAIConfig, GeminiConfig], Field(discriminator="provider")
]


class Config(BaseModel):
    """插件主配置"""

    # --- 通用功能设置 (与具体账户无关) ---
    summary_max_length: int = Field(1000, description="总结内容的最大长度限制")
    summary_min_length: int = Field(50, description="总结内容的最小长度限制")
    summary_cool_down: int = Field(0, description="单个用户调用总结功能的冷却时间(秒)")
    summary_in_png: bool = Field(True, description="是否将总结结果以图片形式发送")

    # --- 异步任务队列设置 ---
    summary_max_queue_size: int = Field(
        10, description="等待处理的总结任务队列最大数量"
    )
    summary_queue_timeout: int = Field(
        300, description="任务在队列中等待处理的超时时间(秒)"
    )
    summary_queue_workers: int = Field(2, description="同时处理总结任务的最大并发数")

    # --- AI 账户列表 ---
    ai_accounts: list[AIProviderConfig] = Field(
        min_length=1,
        validate_default=True,  # 确保至少配置了一个账户
        description="AI服务商账户配置列表",
    )
    # --- 默认账户 ---
    default_account_nickname: str | None = Field(
        None, description="默认使用的账户别名。如果未设置，将使用列表中的第一个账户。"
    )

    @field_validator("ai_accounts", mode="before")
    @classmethod
    def transform_dict_to_list(cls, v: Any) -> list[AIProviderConfig]:
        """
        在验证前，将从 .env 解析出的字典 {'0': {...}, '1': {...}} 转换成列表 [{...}, {...}]
        如果输入已经是列表 (来自 .toml/.json)，则直接返回。
        """
        result = v
        if isinstance(result, dict):
            # 按 '0', '1', '2'... 排序并提取值
            result = [v[k] for k in sorted(v.keys(), key=int)]
        return result

    @model_validator(mode="after")
    def check_accounts_and_default(self) -> "Config":
        # 检查 nickname 是否唯一
        nicknames = [acc.nickname for acc in self.ai_accounts]
        if len(nicknames) != len(set(nicknames)):
            raise ValueError("配置项 'ai_accounts' 中的 'nickname' 必须是唯一的。")

        # 如果设置了 default_account_nickname，检查它是否存在
        if (
            self.default_account_nickname
            and self.default_account_nickname not in nicknames
        ):
            raise ValueError(
                f"设置的默认账户别名 '{self.default_account_nickname}' "
                f"在 'ai_accounts' 列表中不存在。"
            )
        return self


config = get_plugin_config(Config)
