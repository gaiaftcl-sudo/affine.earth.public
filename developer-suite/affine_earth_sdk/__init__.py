"""Affine.Earth developer SDK — HTTPS clients for MCP, OpenAI /v1, language games, OpenUSD."""

from .client import AffineClient, AffineConfig
from .mcp import MCPClient
from .openai_v1 import OpenAIV1Client
from .language_games import LanguageGamesClient
from .umc import UMCClient
from .openusd import OpenUSDClient

__all__ = [
    "AffineClient",
    "AffineConfig",
    "MCPClient",
    "OpenAIV1Client",
    "LanguageGamesClient",
    "UMCClient",
    "OpenUSDClient",
]
__version__ = "0.1.0"
