from __future__ import annotations

import telebot
from dotenv import load_dotenv
import os
from collections import OrderedDict, namedtuple
from config import LANGUAGE, MAX_USERS, MAX_TIME, MAX_SESSION_TIME, MAX_IDLE_TIME
# config.TEST_EXTN stores an extension of files containing questionnaires ("txt" by default)
# config.TEST_DIR stores a directory (full path) where questionnaires are located
from config import TEST_EXTN, TESTS_DIR
import time
from typing import Sequence, Callable, Any, Literal
from typing import NamedTuple
from quiz import Quiz
from buttons import BTN_NEXT, BTN_OK, BTN_QUIT, BTN, make_inline_kb, make_inline_buttons
from errors import MaximumUsersNumberReached
from quiz import Scale
from commands import Commands, all_commands

# CREDENTIALS
load_dotenv()
TOKEN = os.getenv('TOKEN')
if TOKEN is None:
    raise ValueError(f'TOKEN {TOKEN} is not valid')

bot = telebot.TeleBot(TOKEN)
all_quizes = {}

BUTTONS = {"next": BTN_NEXT,
           "ok": BTN_OK,
           "quit": BTN_QUIT,
           }


def first(d: Sequence):
    """
    Returns the first element of any sequence
    """
    return next(iter(d))


class User:
    users: OrderedDict[int, RegisteredUser] = OrderedDict()  # dictionary of all instances of the class

    @classmethod
    def register_user(cls, user: User) -> None:
        """
        Adds a new user to class attribute `users` if the maximum number of users is not reached

        :param user: instance of the ``User`` class
        :return: None
        """
        if user.user_id in cls.users:
            del cls.users[user.user_id]
            cls._add_new_user(user)
            return None
        if len(cls.users) < MAX_USERS:
            cls._add_new_user(user)
            return None
        if cls._inactive_user() is None:
            raise MaximumUsersNumberReached(MAX_USERS, "few")
        else:
            inactive_user = cls._inactive_user()
            inactive_user.session_over(inactive_user.chat_id)
            cls._add_new_user(user)
            return None

    @classmethod
    def _add_new_user(cls, user: User):
        cls.users[user.user_id] = RegisteredUser(user, time.time())

    @classmethod
    def _is_user_inactive(cls, user: User) -> bool:
        current_time = time.time()
        return all(((current_time - user.enter_time) > MAX_SESSION_TIME,
                    (current_time - user.last_activity_time) > MAX_IDLE_TIME))

    @classmethod
    def _inactive_user(cls) -> User | None:
        """

        :return: returns inactive user if such one is detected, or None
        """
        first_user_id = first(cls.users)
        if cls._is_user_inactive(cls.users[first_user_id].ref):
            return cls.users[first_user_id].ref
        return None # if there is no inactive user

    @classmethod
    def unregister_user(cls, user_id: int):
        cls.users.pop(user_id)

    def __init__(self, user_id: int, chat_id: int):
        self.user_id = user_id
        self.chat_id = chat_id
        self.scores = None
        self.quiz = None
        self.question_id = None
        self.answer_id = None
        self.__class__.register_user(self)
        self._on_press_ok = lambda x: True
        self.last_activity_time = self.enter_time

    @property
    def enter_time(self) -> float:
        return self.__class__.users[self.user_id].timestamp

    def start_quiz(self, title: str, chat_id: int):
        self.last_activity_time = time.time()
        if title not in all_quizes:
            return
        # print(f'Quiz start for user: {self.user_id}')
        QUIZ_STARTING_MSG = {"EN": "quiz is starting...",
                             "RU": "загружается текст опросника..."}[LANGUAGE]
        remove_menu(chat_id, QUIZ_STARTING_MSG)
        quiz = all_quizes[title]
        self.quiz = quiz
        self.scores = {}
        self.question_id = None
        scale_id: str
        scale: Scale
        for scale_id, scale in self.quiz.scales.items():
            self.scores[scale_id] = Scale(name=scale.name)
        start_quiz_msg = quiz.title + "\n" + quiz.description
        show_msg(chat_id, msg=start_quiz_msg, btns=[BTN_NEXT, BTN_QUIT])

    def next_question(self, chat_id: int):
        self.last_activity_time = time.time()
        if self.quiz is None:
            return
        if self.question_id == len(self.quiz.questions) - 1:
            self.show_results(chat_id)
        else:
            try:
                self.question_id += 1
            except TypeError:  # if this is the first question, self.question_id is None
                self.question_id = 0
            question_num = str(self.question_id)
            prefix = f'({str(self.question_id+1)}/{str(len(self.quiz.questions))}) '
            question_text: str = prefix + self.quiz.question_text(self.question_id)
            answers_text = self.quiz.answers_text(self.question_id)
            btns = self._answers_buttons(question_num, answers_text)
            show_msg(chat_id, msg=question_text, btns=btns)

    @staticmethod
    def _answers_buttons(question_num: str, answers_text) -> list[telebot.types.InlineKeyboardButton]:
        prefix = "Q#" + question_num + "_A#"
        btns_txt = []
        btns_cb_data = []
        for ans_num, text in answers_text:
            print(text, ans_num)
            btns_txt.append(text)
            btns_cb_data.append(prefix + str(ans_num))
        return make_inline_buttons(btns_txt, btns_cb_data)

    def session_over(self, chat_id: int):
        self._say_goodbye(chat_id)
        self.__class__.unregister_user(self.user_id)

    def show_results(self, chat_id: int):
        self.last_activity_time = time.time()
        results: str = self.quiz.get_result(self.scores)
        show_msg(chat_id, msg=results, btns=[BTN_OK,])
        self._on_press_ok = self.session_over

    def update_scores(self, question_id: int, answer_id: int):
        new_scores: dict[str, int] = self.quiz.get_answer_scores(question_id, answer_id)
        for scale, score in new_scores.items():
            self.scores[scale].value += score
        print(self.scores)

    def _say_goodbye(self, chat_id):
        msg = {"RU": "Ваш сеанс работы завершён. Для возобновления работы выберите команду /start .",
               "EN": "Your session is over. Please, select a /start command to start a new session"}[LANGUAGE]
        show_msg(chat_id, msg=msg)

    def send_ok(self, chat_id: int):
        self._on_press_ok(chat_id)

    def reset_user_data(self):
        self.scores = None
        self.quiz = None
        self.question_id = None
        self.answer_id = None


class RegisteredUser(NamedTuple):
    ref: User
    timestamp: float


class Menu(NamedTuple):
    msg: str
    kb: telebot.types.ReplyKeyboardMarkup
    handler: Callable


start_menu = None


def show_msg(chat_id: int, msg: str,
             btns: list[telebot.types.InlineKeyboardButton] | None = None,
             parse_mode: Literal['markdown', 'html', 'plain'] = "markdown") -> None:
    if '\\n' in msg:
        msg = cr_processing(msg)
    if btns is not None:
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(*btns)
    else:
        markup = telebot.types.ReplyKeyboardRemove()
    msg = bot.send_message(chat_id, msg, reply_markup=markup, parse_mode=parse_mode)


def cr_processing(s: str) -> str:
    return s.replace('\\n','\n')


def show_menu(message: telebot.types.Message, menu: Menu) -> None:
    chat_id = message.chat.id
    bot.send_message(chat_id, menu.msg, reply_markup=menu.kb)
    bot.register_next_step_handler(message, menu.handler)


def remove_menu(chat_id: int, msg: str = "...") -> None:
    markup = telebot.types.ReplyKeyboardRemove(selective=False)
    message = bot.send_message(chat_id, msg,
                     reply_markup=markup, parse_mode="html")
    del_msg(chat_id, message.id)


def del_msg(chat_id: int, message_id: int):
    try:
        bot.delete_message(chat_id=chat_id, message_id=message_id)
    except:
        print(f'{message_id} doesn\'t exist')


@bot.message_handler(commands=['start'])
def starting_menu(message):
    """
    To be called when ``/start`` command is entered.

    Creates a `user` instance of `User` class
    by calling ``make_new_user`` function.

    If `user` is instantiated without any exceptions,
    a start menu will be shown (``else`` block).

    :type message: telebot.types.Message
    """
    try:
        make_new_user(message.from_user.id, message.chat.id)
    except MaximumUsersNumberReached:
        maximum_users_number_reached_notification = {"RU": "Достигнуто максимально количество пользователей, "
                                                           "попробуйте позднее",
                                                     "EN": "Max number of users is reached. Try again later"}[LANGUAGE]
        show_msg(message.chat.id, msg=maximum_users_number_reached_notification)
    else:  # if everything is ok, and user is instantiated
        show_menu(message, start_menu)


@bot.message_handler(commands=all_commands)
def commands_processing(message: telebot.types.Message):
    chat_id = message.chat.id

    # extracting a command
    command = None
    entity: telebot.types.MessageEntity
    for entity in message.entities:
        if entity.type == 'bot_command':
            command = message.text[entity.offset + 1:entity.length + entity.offset]
            break
    if command is None:
        return  # no command discovered

    # commands executing
    if command == Commands.DISCLAIMER.value:
        disclaimer_txt = {'RU': 'Представленная здесь информация не является профессиональной консультацией '\
                          'и не заменяет обращения к специалисту. Не воспринимайте результаты тестов как '\
                          'истину в последней инстанции. Вся информация размещена в информацонных и развлекательных '\
                          'целях.',
                          'EN': 'Information in this chatbot is not a professional advice, and is not any '\
                          'kind of substitution for seeking a professional advice. Please, do not take test '\
                          'results as ultimate truth. All information is presented for informational '\
                          'and entertainment purposes.'
                          }[LANGUAGE]
        show_msg(chat_id, msg=disclaimer_txt)
        return
    if command == Commands.AUTHOR.value:
        about_author_txt = {'RU': 'Разработчик чатбота @EdFromChelly. Обращайтесь по вопросам развития чатбота, '\
                            'присылайте сообщения о выявленных ошибках, предложения новых тестов.\n' \
                            'Заказывайте разработку своего чатбота :).',
                            'EN': 'This chatbot is developed by @EdFromChelly. Send a message regarding a '\
                            'development of this chatbot, report about errors discovered by you, offer new '\
                            'tests (questionnaire). \nOrder your own chatbot:).'}[LANGUAGE]
        show_msg(chat_id, msg=about_author_txt)
        return
    if command == Commands.CREDITS.value:
        credits_txt = {'RU':'Разработчик благодарит за профессиональную помощь в развитии бота телеграм-каналы '\
                       '@mariamalko и @psyhologia',
                       'EN':'A developer of this chatbot appreciates telegram-channels @mariamalko and '\
                       '@psyhologia for professional help with the chatbot\'s development'}[LANGUAGE]
        show_msg(chat_id, msg=credits_txt)
        return
    if command == Commands.QUIT.value and message.from_user.id in User.users:
        User.users[message.from_user.id].ref.session_over(chat_id)
    elif command == Commands.MENU.value:
        if message.from_user.id in User.users:
            User.users[message.from_user.id].ref.reset_user_data()
            show_menu(message, start_menu)
        else:
            starting_menu(message)


@bot.callback_query_handler(func=lambda call: call.data in BUTTONS.keys())
def standard_buttons_handler(query: telebot.types.CallbackQuery):
    """
    When one of the standard buttons (*OK*, *Next*, *Quit*) is pressed,
    this function handles it.

    Standard buttons are hardcoded in `BUTTONS` dictionary.

    :param query: telebot.types.CallbackQuery
    """
    bot.answer_callback_query(query.id)
    if query.from_user.id not in User.users:
        unregistered_user_input(query.from_user.id, query.message.chat.id)
        return
    if query.data == "next":
        next_pressed(query)
    elif query.data == "quit":
        quit_pressed(query)
    elif query.data == "ok":
        ok_pressed(query)


def unregistered_user_input(user_id, chat_id):
    msg = {"RU": "Для начала работы введите команду /start",
           "EN": "To start a session type the command /start"}[LANGUAGE]
    show_msg(chat_id, msg=msg, btns=None)


def next_pressed(query: telebot.types.CallbackQuery):
    del_msg(query.message.chat.id, query.message.message_id)
    User.users[query.from_user.id].ref.next_question(query.message.chat.id)


def quit_pressed(query):
    del_msg(query.message.chat.id, query.message.message_id)
    User.users[query.from_user.id].ref.session_over(query.message.chat.id)


def ok_pressed(query):
    User.users[query.from_user.id].ref.send_ok(query.message.chat.id)


def make_new_user(user_id: int, chat_id: int):
    User(user_id, chat_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("Q#"))
def answer_buttons_handler(query: telebot.types.CallbackQuery):
    """
    When a button with answer option is pressed, this function
    handles it.

    :param query: telebot.types.CallbackQuery
    """
    bot.answer_callback_query(query.id)
    if query.from_user.id not in User.users:
        unregistered_user_input(query.from_user.id, query.message.chat.id)
        return
    question_num, answer_num = _parse_answer_callback(query.data)
    User.users[query.from_user.id].ref.update_scores(question_num, answer_num)
    del_msg(query.message.chat.id, query.message.message_id)
    User.users[query.from_user.id].ref.next_question(query.message.chat.id)


def _parse_answer_callback(callback_data: str) -> tuple[int, int]:
    question_num, answer_num = callback_data.split("_")
    question_num = int(question_num[2:])
    answer_num = int(answer_num[2:])
    return question_num, answer_num


def get_tests_filenames() -> list[str]:
    """
    Returns list of filenames of questionnaires using global variables TESTS_DIR and TEST_EXTN

    :return: list of filenames of questionnaires
    """
    pwd = os.getcwd()
    tests_full_path = os.path.join(pwd, TESTS_DIR)
    filenames = [os.path.join(tests_full_path, name)
                 for name in os.listdir(tests_full_path)
                 if name.endswith(TEST_EXTN)]
    return filenames


def initialize():
    global start_menu
    for name in get_tests_filenames():  # iterate over filenames of questionnaires
        quiz = Quiz.quiz_from_file(name)
        all_quizes[quiz.title] = quiz
    start_message = {"RU": "В этом чатботе можно пройти несколько проверенных психологических тестов.\n"
                           "Выбирите тест из списка ниже.",
                     "EN": "You can take few psychological assessments (test) using this chatbot.\n"
                           "Please, choose a test from the list below."}[LANGUAGE]
    start_menu_buttons = list(map(telebot.types.KeyboardButton,
                                  [title for title in all_quizes]))
    start_kb = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True,
                                                 resize_keyboard=True,
                                                 row_width=1, ).add(*start_menu_buttons)
    start_menu = Menu(msg=start_message,
                      kb=start_kb,
                      handler=lambda msg: User.users[msg.from_user.id].ref.start_quiz(msg.text, msg.chat.id))
    return start_menu




if __name__ == "__main__":
    start_menu = initialize()
    bot.infinity_polling()
