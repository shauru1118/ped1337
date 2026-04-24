import flask

app = flask.Flask(__name__)


@app.route("/")
def root():
    res = f"<h1>Bot: {bot}</h1>\n<h1>ID: {bot.bot_id}</h1>\n<h1>{bot.exc_info}</h1>"
    # for k, v in bot.current_states:

    return res


if __name__ == "__main":
    app.run("0.0.0.0", port=7777, debug=True)


from tgbot import bot
