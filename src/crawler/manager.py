import time

import requests
from pyrogram import Client

from worker import Worker


userbot = Client("crawler")
userbot.start()
worker = Worker(userbot)

add_links = [
]

while True:
    response = requests.get("http://127.0.0.1:8000/get_url")

    if response.status_code != 200:
        print(response.reason)
        break
    link = response.json()["url"]
    # link = add_links.pop()
    print("get link", link)
    link_info, links = worker.process_telegram_link(link)
    print("result", link_info, len(links))
    if type(link_info) is str:
        response = requests.post("http://127.0.0.1:8000/mark_url", params={"url": link})
    else:
        response = requests.put("http://127.0.0.1:8000/channel", json={"channel_info": link_info, "channel_links": links if links else []})
    if response.status_code >= 300:
        print(response.reason)
        break

    # Flood prevention
    time.sleep(60)
