from __future__ import annotations

import telebot
from config import LANGUAGE

BTN = telebot.types.InlineKeyboardButton

button_text = {"quit": {"RU": "Выйти",
                        "EN": "Quit", },
               "ok": {"RU": "OK",
                      "EN": "OK", },
               "next": {"RU": "Дальше",
                        "EN": "Proceed", }
               }


def make_button(key: str, language=LANGUAGE):
    return BTN(button_text[key][language], callback_data=key)


BTN_QUIT = make_button("quit")

BTN_OK = make_button("ok")

BTN_NEXT = make_button("next")


def make_inline_buttons(buttons_text: list[str],
                        buttons_callback_data: list[str]) -> list[telebot.types.InlineKeyboardButton]:
    return [BTN(text, callback_data=cb_data) for text, cb_data in zip(buttons_text, buttons_callback_data)]


def make_inline_kb(buttons_text: list[str], buttons_callback_data: list[str],
                   row_width: int = 1) -> telebot.types.InlineKeyboardMarkup:
    btns = make_inline_buttons(buttons_text, buttons_callback_data)
    return telebot.types.InlineKeyboardMarkup(*btns, row_width=row_width)

