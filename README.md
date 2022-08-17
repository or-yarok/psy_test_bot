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

#### ANSWERS

If different questions of your questionnaire have various set of options of answer or answers are equal for each questions but have different scores for questionnaire's scale(s) you should include one-line block "ANSWERS SPECIFIC". In this case answer options for each question shall be included in the relevant QUESTION block.

If options of answers are identical for all questions and have the same scores you can include all answer options in this block. In this case the first line of this block must contain "ANSWERS COMMON". Each line below must contain:
* asnwer option 
* at least one space
* enclosed in curly brackets, scales named and scores (one space between a scale name and a number which shall be added to this scale if a user chooses this answer option). Pairs of scale name-scores shall be separated from each other by commas (if you have more then a single scale). For exanple:
```{scale1 1, scale2 -1, scale3 0}```.

#### QUESTION

First list of this block must contain the keyword QUESTION and a text of a question, which is separated from the keyword by a space.

If you have specific answer options for each question you must include answer options in the QUESTION block in the same way as described above for ANSWERS block.

Each question of your questionnaire shall be included in a separate QUESTION block.

#### RESULTS

This block contains interpretation of test results depending on values of scales (scores for each scale). Each interpretation (result) takes two lines:
* the first one contains scale name and interval of values (scores); interval boundaries are devided by three dots `...`; if one of boundaris is omitted it is interpreted as 'less than' (left boundary is omitted) or 'greater than' (right boundary is omitted);
* the second one contains a text of interpretation for this interval of scores enclosed in curly brackets.

## config.py

Configuration file `config.py` contains few settings:

* `LANGUAGE` allows to choose a language of bot interface (not language of questionnaires). At the moment, 'RU' for Russian and 'EN' for English are supported.
* `MAX_USERS` stores maximum number of users at the same time
* `MAX_SESSION_TIME` and `MAX_IDLE_TIME` (both are in seconds): if maximum number of users is reached, the user who exceeds maximum duration of a session (`MAX_SESSION_TIME`) and maximum duration of inactivity (`MAX_IDLE_TIME`) will be off when new user will come
* `TESTS_DIR` stores name of directory where files with questionnaires are located
* `TEST_EXTN` contains a file extension of files with questionnaires (`txt` by default).
