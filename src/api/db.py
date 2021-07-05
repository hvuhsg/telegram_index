from datetime import datetime, timedelta

from qwhale_client import APIClient
from pymongo import DESCENDING


class DB:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            raise RuntimeError(f"{cls.__name__} is not initialized")
        return cls._instance

    def __init__(self):
        self.__client = APIClient(token="bd929064a9aa4694394c33ac48400a04:d4a6d7f71deab8b49ba059c8a2a45963")
        self.__db = self.__client.get_database()
        self.__client.activate_database()

        self.channels = self.__db.get_collection("channels")
        self.channels.create_index([("url", 1)], unique=True)

        self.mentions = self.__db.get_collection("mentions")
        self.mentions.create_index([("url", 1)], unique=True)

        self.__class__._instance = self

    def new_channel(self, channel_dict) -> bool:
        channel = self.channels.find_one({"url": channel_dict["url"]})
        if channel is None:
            self.channels.insert_one(channel_dict)
            self.mentions.update_one(
                {"url": channel_dict["url"]},
                {"$inc": {"mentions": 1}, "$set": {"processed": True, "processing": False}}
            )
            return True
        else:
            self.channels.replace_one({"url": channel_dict["url"]}, replacement=channel_dict)
            return False

    def update_channels_mentions(self, links: list):
        found_links = self.mentions.find({"url": {"$in": links}}, {"url": 1})
        found_links = [link["url"] for link in found_links]
        self.mentions.update_many({"url": {"$in": found_links}}, {"$inc": {"mentions": 1}})
        if not found_links:
            found_links = []
        for link in found_links:
            links.remove(link)

        new_mention = {"mentions": 1, "processing": False, "processed": False}
        documents = [{"url": link, **new_mention} for link in links]
        if documents:
            self.mentions.insert_many(documents)

    def update_mention(self, url):
        self.mentions.update_one({"url": url}, {"$set": {"processing": False, "processed": True}})

    def pull_url_for_process(self):
        return self.mentions.find_one_and_update(
            filter={
                "processed": {"$ne": True},
                "$or": [
                    {"processing": {"$ne": True}},
                    {"process_date": {"$lt": datetime.utcnow()-timedelta(hours=1)}}
                ]
            },
            update={"$set": {"processing": True, "process_date": datetime.utcnow()}}
        )

    def get_suggested_channels(self, uid: int, limit: int = 10):
        return list(
            self.channels.find(
                {f"marks.{uid}": {"$exists": False}},
                {"marks": 0, "_id": 0}
            ).sort([("total_views", DESCENDING)]).limit(limit)
        )

    def set_action(self, uid: int, post_id: int, action: int):
        if type(uid) is not int:
            raise TypeError("UID must be an int for security reason")
        self.channels.update_one({"id": post_id}, {"$set": {f"marks.{uid}": action}})

    def load_user_saved(self, uid: int):
        if type(uid) is not int:
            raise TypeError("UID must be an int for security reason")
        return list(self.channels.find({f"marks.{uid}": 1}, {"marks": 0, "_id": 0}))

    def close(self):
        self.__client.deactivate_database()
