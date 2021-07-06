from fastapi import FastAPI

from objects import Channel
from db import DB

app = FastAPI(title="TelegramIndex")


@app.on_event("startup")
async def startup():
    DB()  # init singleton


@app.on_event("shutdown")
async def shutdown():
    db = DB.get_instance()
    db.close()


@app.put("/channel", status_code=201)
async def upload_channel_info(channel_info: Channel, channel_links: list = None):
    db: DB = DB.get_instance()
    if channel_info.url in channel_links:
        channel_links.remove(channel_info.url)

    is_new_channel = db.new_channel(channel_info.dict())
    if is_new_channel and channel_links:
        db.update_channels_mentions(channel_links)
    return {"Created": True}


@app.get("/get_url")
async def get_url():
    db: DB = DB.get_instance()
    url_job = db.pull_url_for_process()
    if url_job is None:
        return {"url": None}, 404
    return {"url": url_job["url"]}


@app.post("/mark_url")
async def mark_url(url: str):
    db: DB = DB.get_instance()
    db.update_mention(url)
    return {"marked": True}


@app.get("/suggestions")
async def get_post_suggestions(uid: int, count: int = 10):
    db: DB = DB.get_instance()
    channels = db.get_suggested_channels(uid=uid, limit=count)
    posts = []
    for channel in channels:
        posts.append(
            {
                "id": channel["id"],
                "name": channel["name"],
                "description": channel["description"],
                "subscribers": channel["subscribers"],
                "messages": channel["total_messages"],
                "url": channel["url"],
            }
        )
    return {"suggestions": posts}


@app.post("/post/user_action")
async def user_action(uid: int, post_id: int, action: int):
    db: DB = DB.get_instance()
    db.set_action(uid, post_id, action)
    return {"OK": True}


@app.get("/user/saved")
async def get_saved_posts(uid: int):
    db: DB = DB.get_instance()
    channels = db.load_user_saved(uid)
    posts = []
    for channel in channels:
        posts.append(
            {
                "id": channel["id"],
                "name": channel["name"],
                "description": channel["description"],
                "subscribers": channel["subscribers"],
                "messages": channel["total_messages"],
                "url": channel["url"],
            }
        )
    return {"posts": posts}
