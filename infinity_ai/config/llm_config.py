"""
LLM配置 - Claude API配置
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator
import os


class LLMConfig(BaseModel):
    """LLM配置"""

    # API配置
    api_key: Optional[str] = Field(
        default=None,
        validate_default=True,
        description="Claude API密钥"
    )
    api_base_url: Optional[str] = Field(
        default=None,
        validate_default=True,
        description="API基础URL（自定义代理时使用）"
    )
    # 认证方式：api_key 使用 X-Api-Key 头；bearer 使用 Authorization: Bearer（兼容 OpenAI 风格代理）
    api_auth_type: Literal["api_key", "bearer"] = Field(
        default="api_key",
        validate_default=True,
        description="认证方式"
    )

    @field_validator("api_base_url", mode="before")
    @classmethod
    def set_api_base_url(cls, v):
        if v is None or v == "":
            return os.getenv("BASE_URL")
        return v

    @field_validator("api_auth_type", mode="before")
    @classmethod
    def set_api_auth_type(cls, v):
        if v and v != "api_key":
            return v
        env_val = os.getenv("API_AUTH_TYPE", "api_key").lower()
        if env_val in ("bearer", "token"):
            return "bearer"
        return "api_key"

    # 模型配置
    model: str = Field(
        default="glm-5",
        description=f"使用的glm模型"
    )
    max_tokens: int = Field(default=4096, description="最大token数")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="温度参数")

    # 请求配置
    request_timeout: int = Field(default=1200, description="请求超时时间（秒）")
    max_retries: int = Field(default=3, description="API请求重试次数")

    @field_validator("api_key", mode="before")
    @classmethod
    def set_api_key(cls, v):
        """如果没有提供API key，从环境变量获取"""
        if v is None:
            v = os.getenv("ANTHROPIC_API_KEY")
        return v

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v):
        """验证API key格式（宽松验证）"""
        # 如果没有提供API key，允许None（后续会检查）
        if v is None:
            return v
        # API key通常是字符串，做一些基本检查
        if not isinstance(v, str):
            raise ValueError("API key must be a string")
        if len(v) < 10:
            raise ValueError("API key seems too short")
        return v

    def is_valid(self) -> bool:
        """检查配置是否有效"""
        return self.api_key is not None and len(self.api_key) > 0

    def get_client_kwargs(self) -> dict:
        """获取 Anthropic 客户端的初始化参数

        根据 api_auth_type 选择认证方式：
        - api_key: 使用 X-Api-Key 头（Anthropic 官方）
        - bearer: 使用 Authorization: Bearer 头（兼容 OpenAI 风格代理）
        """
        if self.api_auth_type == "bearer":
            kwargs = {"auth_token": self.api_key, "api_key": None}
        else:
            kwargs = {"api_key": self.api_key}
        if self.api_base_url:
            kwargs["base_url"] = self.api_base_url
        return kwargs