from enum import Enum


class Purpose(str, Enum):
    CHAT = "chat"
    EMBEDDING = "embedding"
