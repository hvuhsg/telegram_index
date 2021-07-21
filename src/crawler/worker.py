from pyrogram import Client
from pyrogram.types import Chat, Message
from pyrogram.raw.types import InputChannel
from pyrogram.raw.base.messages import ChatFull
from pyrogram.raw.functions.messages import GetFullChat
from pyrogram.raw.functions.channels.get_full_channel import GetFullChannel
from pyrogram.errors import BadRequest

EMA_SMOOTH_FACTOR = 0.5


class Worker:
    def __init__(self, userbot: Client):
        self.userbot = userbot

    @staticmethod
    def url_to_username(url: str):
        return "@" + url[url.rfind('/') + 1:]

    @staticmethod
    def calculate_ema(total_values: int, current_ema: float, new_value):
        if current_ema is None:
            return new_value
        if new_value is None:
            return current_ema
        smooth = 1 / EMA_SMOOTH_FACTOR
        return (current_ema * total_values * smooth + new_value) / (total_values * smooth + 1)

    @staticmethod
    def is_telegram_channel_link(link: str) -> bool:
        options = [
            "t.me/",
            "http://t.me/",
            "https://t.me/",
            "telegram.me/",
            "http://telegram.me/",
            "https://telegram.me/",
        ]
        return any(map(lambda t: link.startswith(t), options)) \
               and "start=" not in link \
               and link[-3:].lower() != "bot" \
               and "/setlanguage/" not in link

    @staticmethod
    def clean_link(link: str) -> str:
        end_route = link[link.rfind("/") + 1:]  # t.me/channel_name/<number> <- it's post link
        if end_route.isdecimal():
            link = link[:link.rfind("/")]
        link = link.replace("http:", "https:")
        link = link.replace("telegram.me/", "t.me/")
        if link.startswith("t.me/"):
            link = "https://" + link
        return link

    def find_channel_links(self, message: Message):
        links = set()
        allowed_entity_types = ("url", "mention", "text_link")

        def add_to_links(is_text, ent):
            if ent.type not in allowed_entity_types:
                return
            if ent.type in ("url", "mention"):
                if is_text:
                    link = message.text[ent.offset:ent.offset + ent.length]
                else:
                    link = message.caption[ent.offset:ent.offset + ent.length]
                if ent.type == "mention":
                    link = f"https://t.me/{link[1:]}"
            elif ent.type == "text_link":
                link = ent.url
            if self.is_telegram_channel_link(link):
                link = self.clean_link(link)
                links.add(link)

        if message.entities:
            for ent in message.entities:
                add_to_links(True, ent)
        if message.caption_entities:
            for ent in message.caption_entities:
                add_to_links(False, ent)
        return links

    def process_messages(self, chat: Chat):
        total_messages = 0
        total_views = 0
        files = 0
        photos = 0
        videos = 0
        audio = 0
        ema_views = None
        start_post_date = None
        last_post_date = None
        links = set()
        for message in self.userbot.iter_history(chat.id, reverse=True):
            total_messages += 1
            if start_post_date is None:
                start_post_date = message.date
            ema_views = self.calculate_ema(total_messages, ema_views, message.views)
            if isinstance(message.views, int):
                total_views += message.views
            if message.document:
                files += 1
            elif message.photo:
                photos += 1
            elif message.video or message.video_note:
                videos += 1
            elif message.audio or message.voice:
                audio += 1
            links.update(self.find_channel_links(message))
            last_post_date = message.date

        messages_info = {
            "total_messages": total_messages,
            "total_views": total_views,
            "ema_views": ema_views if ema_views else 0,
            "first_post_date": start_post_date,
            "last_post_date": last_post_date,
            "files": files,
            "photos": photos,
            "videos": videos,
            "audio": audio,
        }
        return messages_info, list(links)

    def process_telegram_link(self, channel_url):
        username = self.url_to_username(channel_url)
        print(username)

        try:
            chat: Chat = self.userbot.get_chat(username)
        except BadRequest:
            return "", []
        if chat.type != "channel" or chat.is_restricted:
            return chat.type, []
        # chat_id = int(str(chat.id)[4:])
        # full_channel: ChatFull = self.userbot.send(
        #     data=GetFullChat(chat_id=chat_id)
        # )
        # print(full_channel.full_chat)

        channel_info = {"url": channel_url, "name": chat.title, "id": chat.id, "description": chat["description"],
                        "username": chat["username"], "is_verified": chat["is_verified"],
                        "is_restricted": chat["is_restricted"], "is_creator": chat["is_creator"],
                        "is_scam": chat["is_scam"],
                        "is_fake": chat["is_fake"], "subscribers": chat["members_count"], "type": chat.type}
        messages_info, links = self.process_messages(chat)
        channel_info.update(messages_info)
        if channel_url in links:
            links.remove(channel_url)
        return channel_info, links


if __name__ == "__main__":
    userbot = Client("crawler")
    userbot.start()
    worker = Worker(userbot)
    worker.process_telegram_link("https://t.me/yehoyadachannel")
