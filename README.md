# Telegram bot for psychological testing

Although, the primary purpose of this script is psychological testing, it can be used for any questionnaires, tests, quizes, etc. via telegram chatbot.

This project allows to create telegram bots with various tests and questionnaires.

The specific implementation of this project (in Russian) you can try at [@tg_psychotest_bot](http://t.me/tg_psychotest_bot).

---
## Bot's token

In order to connect this script with your telegram bot you need to obtain the bot's token at [@BotFather](https://t.me/BotFather). See detailed information in [telegram bot docs](https://core.telegram.org/bots).

You may store the bot's token in the environmental variable or include this credentials into `.env` file. I use `.env` file together with [`dotenv` module](https://pypi.org/project/python-dotenv/). The `.env` is omitted in this repository for privacy purposes.

## Polling vs. Webhook

> There are two mutually exclusive ways of receiving updates for your bot - the `getUpdates` method on one hand and `webhooks` on the other.

   [Telegram Bot API docs](https://core.telegram.org/bots/api#getting-updates)

### Infinitive Polling

Run `psy-test-bot.py` for infinitive polling:
```python
if __name__ == "__main__":
    start_menu = initialize()
    bot.infinity_polling()
```

### Webhook

See [Telegram Bot API docs](https://core.telegram.org/bots/api#setwebhook) how to set and use webhooks.

## Questionnaires

All questionnaires shall be stored in `\tests` folder and have `.txt` file extension. The script discovers all `*.txt` files in `\tests` directory automatically. You can change the default directory and file extension in `config.py` (change the variables `TESTS_DIR` and `TEST_EXTN`).

A valid questionnaire file shall have the specific structure and formatting as describe below.

### Blocks

Blocks are devided by lines starting with "=" character.

Each block starts with a keyword (TITLE, SCALES, DESCRIPTION, ANSWERS, QUESTION, RESULTS). The blocks are described below in the recommended subsequence. It's highly recommended to follow this block sequence. 

#### TITLE

One-line block. The title of a questionnaire follows next to the keyword TITLE, and is separated from the keyword by at least one space.

#### SCALES

The first line of this block contains only the keyword SCALES

Each line below contains a name of the specific scale and its description / name devided by one space.

Even if your questionnaire has only one scale (just a sum of scores according to user's answers), you have to include this scale in file with the questionnaire.

#### DESCRIPTION

Give a short instruction for a user. Indicate an author of the questionnaire (if any).

The first line of this block contains only the keyword DESCRIPTION.

The description itself may include multiple lines and shall be enclosed in curly brackets.




