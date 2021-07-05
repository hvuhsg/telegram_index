class Button:
    def __init__(self, id: int, icon: str, share: bool = False, inline_search: bool = False):
        self.id = id
        self.icon = icon
        self.share = share
        self.inline_search = inline_search
