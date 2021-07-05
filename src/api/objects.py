from typing import Union
from pydantic import BaseModel


class Channel(BaseModel):
    id: int
    name: str
    username: str
    description: Union[str, None]
    url: str
    subscribers: int
    type: str

    is_verified: bool
    is_restricted: bool
    is_creator: bool
    is_scam: bool
    is_fake: bool

    photos: int
    videos: int
    files: int
    audio: int

    total_views: int
    ema_views: float
    total_views: int
    total_messages: int

    first_post_date: int
    last_post_date: int


class Mention(BaseModel):
    url: str
    processing: bool = False
    processed: bool = False

    mentions: int = 1
