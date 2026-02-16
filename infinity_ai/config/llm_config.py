"""
LLM配置 - Claude API配置
"""
from typing import Optional
from pydantic import BaseModel, Field, validator
import os


class LLMConfig(BaseModel):
    """LLM配置"""

    # API配置
    api_key: Optional[str] = Field(default=None, description="Claude API密钥")
    api_base_url: str = Field(
        default=os.getenv('BASE_URL'),
        description="API基础URL"
    )

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

    @validator('api_key', pre=True, always=True)
    def set_api_key(cls, v):
        """如果没有提供API key，从环境变量获取"""
        if v is None:
            v = os.getenv('ANTHROPIC_API_KEY')
        return v

    @validator('api_key')
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