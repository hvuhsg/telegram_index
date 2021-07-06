from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, InlineQueryHandler
from telegram.ext import PicklePersistence

from handlers import on_start, on_help, on_inline_button, on_inline_query


class SuggestionsBot:
    def __init__(self, bot_token):
        self.updater = Updater(bot_token, workers=2, persistence=PicklePersistence(filename="./cache.db"))
        self.dispatcher = self.updater.dispatcher
        self.create_handlers()
        print("Bot started")

    def run(self):
        # Start the bot
        self.updater.start_polling()

        # Run the bot until you press Ctrl-C
        self.updater.idle()

    def create_handlers(self):
        start_handler = CommandHandler("start", callback=on_start)
        self.dispatcher.add_handler(start_handler)

        help_handler = CommandHandler("help", callback=on_help)
        self.dispatcher.add_handler(help_handler)

        inline_handler = CallbackQueryHandler(on_inline_button)
        self.dispatcher.add_handler(inline_handler)

        inline_query_handler = InlineQueryHandler(on_inline_query)
        self.dispatcher.add_handler(inline_query_handler)


def main():
    bot = SuggestionsBot("1801127369:AAG4MlZvXlg8TBMOtpboAoL7VqQlQ24Mok8")
    bot.run()


if __name__ == "__main__":
    main()
