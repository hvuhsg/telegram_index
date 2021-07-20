from datetime import datetime, timedelta

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import CallbackContext

from button import Button
from keyboards import post_keyboard
from client import submit_user_action, get_suggestions_by_user_id, load_saved_posts


def post_to_text(post: dict):
    text = post['name'] + "\n"
    text += f"-" * 100 + "\n"
    text += f"👥 {post['subscribers']}\n"
    text += f"-" * 100 + "\n"
    text += f"💬️ {post['messages']}\n"
    text += f"-" * 100 + "\n"
    text += post['url']
    return text


def load_user_saved_posts(uid: int, context: CallbackContext):
    if context.user_data.get("saved", None) is None:
        context.user_data["saved"] = {}
    posts = load_saved_posts(uid)
    posts_dict = {str(post['id']): post for post in posts}
    context.bot_data["posts"].update(posts_dict)
    context.user_data["saved"].update(posts_dict)


def bump_to_the_top(update: Update, context: CallbackContext):
    try:
        bump_message = update.callback_query.message.reply_text(".")
        bump_message.delete()
    except Exception as EX:
        print("Bump error:", EX)


def update_post(update: Update, context: CallbackContext):
    if not context.user_data.get("suggestions", None):
        suggestions = get_suggestions_by_user_id(user_id=update.effective_user.id)
        context.user_data["suggestions"] = suggestions
    post: dict = context.user_data["suggestions"].pop(0)
    post_text = post_to_text(post)
    context.bot_data["posts"][str(post["id"])] = post
    like = Button(id=f'V-{post["id"]}', icon="✅")
    dislike = Button(id=f'X-{post["id"]}', icon="❌")
    share = Button(id=f"{post['id']}", icon="🗣", share=True)
    my_saved = Button(id="", icon="💾", inline_search=True)
    if update.message and update.message.text.startswith("/"):
        update.message.reply_text(
            post_text, reply_markup=post_keyboard([[dislike, like], [share, my_saved]])
        )
    else:
        update.callback_query.message.edit_text(
            post_text, reply_markup=post_keyboard([[dislike, like], [share, my_saved]])
        )
    if len(context.user_data["suggestions"]) < 5:
        suggestions = get_suggestions_by_user_id(update.effective_user.id)
        context.user_data["suggestions"].extend(suggestions)


def on_start(update: Update, context: CallbackContext):
    if context.bot_data.get("posts", None) is None:
        context.bot_data["posts"] = {}
    if context.user_data.get("saved", None) is None:
        load_user_saved_posts(update.effective_user.id, context)
    update_post(update, context)
    if context.user_data.get("saved", None) is None:
        context.user_data["saved"] = {}


def on_help(update: Update, context: CallbackContext):
    print(update)


def on_inline_button(update: Update, context: CallbackContext):
    button_id = update.callback_query.data

    last_interaction_date = context.user_data.get("last_interaction")
    if last_interaction_date and datetime.utcnow() - last_interaction_date > timedelta(hours=1):
        bump_to_the_top(update, context)
    context.user_data["last_interaction"] = datetime.utcnow()

    post_id = button_id[button_id.find("-") + 1:]
    post_name = context.bot_data["posts"][post_id].get("username")
    if button_id.startswith("V"):
        print("V on", post_name)
        update_post(update, context)
        update.callback_query.answer("Saved! ✅")
        context.user_data["saved"][post_id] = context.bot_data["posts"][post_id]
        submit_user_action(update.effective_user.id, post_id=post_id, saved=True)

    elif button_id.startswith("X"):
        print("X on", post_name)
        if update.callback_query.message is not None:
            update_post(update, context)
        update.callback_query.answer("Discarded! ❌")
        context.user_data["saved"].pop(str(post_id), None)
        submit_user_action(update.effective_user.id, post_id=post_id, saved=False)


def on_inline_query(update: Update, context: CallbackContext):
    if context.user_data.get("saved", None) is None:
        context.user_data["saved"] = {}
    query = update.inline_query.query
    if query in context.bot_data["posts"]:
        post = context.bot_data["posts"][query]
        post_text = post_to_text(post)
        share_button = Button(id=str(post["id"]), icon="🗣", share=True)
        result = [
            InlineQueryResultArticle(
                id=f"{query}",
                input_message_content=InputTextMessageContent(message_text=post_text),
                title=post["name"],
                description=post["description"],
                thumb_url="https://www.edgewaterresearch.com/images/edgewater-logo@2x.png",
                reply_markup=post_keyboard([[share_button]])
            )
        ]
    else:
        results_posts = filter(
            lambda p: query.lower() in p["name"].lower() + p["description"].lower() if p["description"] else "",
            context.user_data["saved"].values()
        )
        result = [
            InlineQueryResultArticle(
                id=post["id"],
                input_message_content=InputTextMessageContent(message_text=post_to_text(post)),
                title=post["name"],
                description=post["description"],
                thumb_url="https://www.edgewaterresearch.com/images/edgewater-logo@2x.png",
                reply_markup=post_keyboard(
                    [
                        [
                            Button(id=str(post["id"]), icon="🗣", share=True)
                        ],
                    ]
                )
            ) for post in results_posts
        ]
    update.inline_query.answer(results=result, cache_time=0)
