import flask
from tgbot import bot

app = flask.Flask(__name__)


@app.route("/")
def root():
    res = f"<h1>Bot: {bot}</h1>\n<h1>ID: {bot.bot_id}</h1>\n<h1>{bot.exc_info}</h1>"
    # for k, v in bot.current_states:

    return res


bot.infinity_polling()
