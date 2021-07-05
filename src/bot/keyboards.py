from telegram import InlineKeyboardMarkup, InlineKeyboardButton


def post_keyboard(button_rows: list):
    keyboard_list = []
    for row in button_rows:
        keyboard_row = []
        for button in row:
            keyboard_row.append(InlineKeyboardButton(
                text=f"{button.icon}",
                callback_data=None if button.share or button.inline_search else button.id,
                switch_inline_query=button.id if button.share else None,
                switch_inline_query_current_chat=button.id if button.inline_search else None,
            ))
        keyboard_list.append(keyboard_row)

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_list)
    return keyboard
