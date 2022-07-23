from __future__ import annotations

from collections import namedtuple

from collections import defaultdict

from collections.abc import Sequence, Generator

from typing import Any, Optional

from dataclasses import dataclass

LANGUAGE = "RU"

QUIZ_FILENAME = "test1.txt"

Answer: namedtuple = namedtuple("Answer", ["id", "text", "scales"])  # datatype for answer options

Question: namedtuple = namedtuple("Question", ["id", "text", "answers"])  # datatype for a quiz question


@dataclass
class Scale:
    """
    datatype for measurement scales
    """
    name: str
    value: int = 0


IntervalPrototype: namedtuple = namedtuple("IntervalPrototype", ["min_", "max_"])


class Interval(IntervalPrototype):
    """A datatype for intervals with min and max fields.
"in" operator is overloaded in order to test if 
the given integer value is within bounds of an interval 
(or equals to its minimum or maximum value).
If upper or lower bound of interval is None it is 
presumed to be +infinity or -infinity, respectively.
"""

    def __contains__(self, item: int) -> bool:
        left = item >= self.min_ if self.min_ is not None else True
        right = item <= self.max_ if self.max_ is not None else True
        return all((left, right))


class ResultRecord():
    """A datatype to store test interpretation for a specific
interval of scores on the given scale (measurements).
"""

    def __init__(self, interval: Interval, description: str):
        self.description = description  # interpretation of test results
        self.interval = interval

    def __repr__(self):
        return (f'{self.__class__.__name__}: {self.interval}, text: "{self.description}"')


class Result(defaultdict):
    """This dictionary-like object will create an empty list by default if a key is absent.
Keys are names of scales (str). Values are list of interpretations for the relevant scale
(list of objects of the ResultRecord type).
"""

    def __init__(self):
        super().__init__(list)

    def update(self, other, **kwargs):
        for k, v in other.items():
            self[k].append(v)

    def get_by_interval(self, k, v: int) -> ResultRecord | None:
        try:
            records = self[k]
        except KeyError:
            return None
        for record in records:
            if v in record.interval:
                return record
        return None


class RawData:
    title: str
    description: str = " "
    questions: list[Question] = None
    answers_type: str = "COMMON"
    answers: Sequence[Answer] = None
    scales: dict[str, Scale] = None
    results: Result = None

    def __repr__(self):
        if self.answers_type == "COMMON":
            answers = "COMMON"
        else:
            answers = self.answers[0].text + '...' + self.answers[-1].text
        return f"title: {self.title} \ndescription: {self.description} \n" +\
               f"number of questions: {len(self.questions)}\n" +\
               f"scales: {self.scales} \nresults: {self.results}\nanswers: " +\
               f"{answers}"


class Quiz:
    """
    Class for quizzes (psychological assessment tests).

    It contains methods to make quiz-objects from a text file and to handle a quiz-object

    """

    @classmethod
    def quiz_from_file(cls, filename: str = QUIZ_FILENAME, comments: str = "#", delimiter: str = "=") -> Quiz:
        """
        Class method of ``Quiz`` class, creates an instance of ``Quiz`` from a special formatted text file.        
        
        :param filename: str (full path to a text file)
        :param comments: str (a line starting with this char(s) will be dropped)
        :param delimiter: str (a line starting with this char(s) divides blocks of information)
        :return: Quiz class instance
        """
        block = []
        # `handlers` maps keywords to handlers (class methods)
        handlers = {"TITLE": __class__.title_handle,
                    "ANSWERS": __class__.answers_handle,
                    "QUESTION": __class__.question_handle,
                    "DESCRIPTION": __class__.description_handle,
                    "SCALES": __class__.scales_handle,
                    "RESULTS": __class__.results_handle,
                    }

        raw_data = RawData()  # stores raw data before creating ``Quiz`` object
        raw_data.results = Result()

        try:
            with open(filename, "r", encoding="utf8") as f:
                for line in f:
                    if line.startswith(comments):  # drop comment lines
                        continue
                    if line.startswith(delimiter):  # If a line starts with a delimiter,
                        if len(block) > 0:          # lines above (`block`) will be handled
                            keyword = block[0].split()[0]
                            if keyword in handlers:
                                handlers[keyword](block, raw_data)  # calls a relevant handler method
                                block = []
                    else:
                        block.append(line.strip())  # adds a line to `block`
        except OSError as err:  # catch an exception if file is not found / no available
            raise FileNotFoundError(f"{filename} not found") from err
        return cls(title=raw_data.title,
                   description=raw_data.description,
                   questions=raw_data.questions,
                   results=raw_data.results,
                   answers=raw_data.answers,
                   scales=raw_data.scales,
                   answers_type=raw_data.answers_type)

    @staticmethod
    def title_handle(lines: str, raw_data: RawData) -> RawData:
        raw_data.title = lines[0][len("title") + 1:]
        return raw_data

    @staticmethod
    def answers_handle(lines: list[str], raw_data: RawData) -> RawData:
        answers_type: str = lines[0][len("answers") + 1:].strip()
        if answers_type == "SPECIFIC":
            raw_data.answers_type = answers_type
            raw_data.answers = None
            return raw_data
        elif answers_type == "COMMON":
            answers = Quiz.answers_list(lines[1:])
            raw_data.answers_type = "COMMON"
            raw_data.answers = answers
            return raw_data

    @staticmethod
    def answers_list(lines: list[str]) -> Sequence[Answer]:
        answers = []
        answer: Answer
        for answer_id, line in enumerate(lines):
            answer_text, raw_scales, _ = Quiz.parse_curly_braces(line)
            answer_scales: dict[str, int] = {}
            for scale in raw_scales.split(","):
                scale_name, scale_score = scale.strip().split()
                answer_scales.update({scale_name.strip(): int(scale_score)})
            answer = Answer(answer_id, answer_text.strip(), answer_scales)
            answers.append(answer)
        return answers

    @staticmethod
    def question_handle(lines: list[str], raw_data: RawData):
        if raw_data.questions is None:
            question_id = 0
            raw_data.questions = []
        else:
            question_id = raw_data.questions[-1].id + 1
        question_text = lines[0][len("question") + 1:].strip()
        if raw_data.answers_type == "SPECIFIC" and len(lines) > 1:
            answers = Quiz.answers_list(lines[1:])
        else:
            answers = None
        raw_data.questions.append(Question(question_id, question_text, answers))
        return raw_data

    @staticmethod
    def description_handle(lines: list[str], raw_data: RawData) -> RawData:
        raw_string: str = "".join(lines)
        _, into_curly, _ = Quiz.parse_curly_braces(raw_string)
        raw_data.description = into_curly
        return raw_data

    @staticmethod
    def scales_handle(lines: list[str], raw_data: RawData):
        lines.pop(0)
        scales = {}
        for line in lines:
            scale_id, scale_name = line.strip().split(maxsplit=1)
            scales[scale_id] = Scale(name=scale_name)
        raw_data.scales = scales
        return raw_data

    @staticmethod
    def results_handle(lines: list[str], raw_data: RawData):
        lines.pop(0)
        raw_string = "".join(lines)
        results = raw_string.split("}")
        for result in results:
            if result.count("{") == 0:
                continue
            header, body = result.split("{", maxsplit=1)
            header = header.strip()
            body = body.strip()
            scale_id, interval_as_string = header.split(maxsplit=1)
            if interval_as_string.startswith("..."):
                min_ = None
                max_ = int(interval_as_string.strip("..."))
            elif interval_as_string.endswith("..."):
                max_ = None
                min_ = int(interval_as_string.strip("..."))
            else:
                min_, max_ = map(int, interval_as_string.split("..."))
            result_record = ResultRecord(interval=Interval(min_, max_), description=body)
            raw_data.results[scale_id].append(result_record)
        return raw_data

    @staticmethod
    def parse_curly_braces(raw_string: str) -> tuple[str, str, str]:
        """
        Parses a text with curly braces and returns a tuple of three strings (``str``):

        * before "{"
        * into "{" and "}"
        * after "}"

        :param raw_string: str (a text with curly braces)
        :return: tuple of 3 (three) strings
        """
        if raw_string.count("{") == 0 or raw_string.count("}") == 0:
            return (raw_string, "", "")
        l: int = raw_string.find("{")
        r: int = raw_string.rfind("}")
        before_curly: str = raw_string[:l].strip("{}")
        into_curly: str = raw_string[l:r].strip("{}")
        after_curly: str = raw_string[r:].strip("{}")
        return (before_curly, into_curly, after_curly)

    def __init__(self, title: str, description: str, questions: Sequence[Question], results: Result,
                 answers: Sequence[Answer] = None, scales: dict = None, answers_type: str = "COMMON", ):
        self.results = results
        self.answers_type = answers_type
        self.questions = questions
        self.title = title
        self.description = description
        self.answers = answers
        self.scales = scales if scales is not None else {"SC": Scale(name="Scores")}

    def question_text(self, question_id: int) -> str:
        """
        Returns a text of the specific question

        :param question_id: int (number of the specific question)
        :return: str (a text of the question)
        """
        try:
            return self.questions[question_id].text
        except IndexError as err:
            print(f'There is no question with {question_id} number')
            print(err)
            return ""

    def answers_text(self, question_id: int) -> Generator[tuple[int, str], Any, Any]:
        """
        Returns a generator which returns a tuple of answer id and answer text one by one
        (for the specific question)

        :param question_id: int (number of the specific question)
        :return: generator -> a para of answer id and answer text for one iteration
        """
        answers = self._get_answers_list(question_id)
        assert isinstance(answers, Sequence) and all([isinstance(answer, Answer) for answer in answers]), 'Answers ' \
                                                                                                          'are not ' \
                                                                                                          'provided'
        return ((answer.id, answer.text) for answer in answers)

    def get_answer_scores(self, question_id: int, answer_id: int) -> list[dict[str, int]]:
        """Returns answer scores for different scales by question id and answer id

        """
        answers = self._get_answers_list(question_id)
        return answers[answer_id].scales

    def _get_answers_list(self, question_id: int):
        """Returns list of answers for a specific question (by question id).

        :param question_id: int
        :return: list of answers
        """
        if self.answers_type == "COMMON":
            return self.answers
        elif self.answers_type == "SPECIFIC":
            try:
                return self.questions[question_id].answers
            except IndexError as err:
                raise IndexError(f'There is no question with id# {question_id}')

    def get_result(self, scores: dict[str, Scale]) -> str:
        results_for_user: str = {"RU": "Ваши результаты:\n",
                                 "EN": "That is your results:\n",
                                 }[LANGUAGE]
        scale_id: str
        score: Scale
        for scale_id, score in scores.items():
            if scale_id in self.results:
                result_record = self.results.get_by_interval(scale_id, score.value)
                about_scale: str = {"RU": "По шкале ",
                                    "EN": "Measurements of the scale ",
                                    }[LANGUAGE]
                results_for_user += f'{about_scale}{self.scales[scale_id].name}: {score.value}\n'
                results_for_user += result_record.description + '\n'
        return results_for_user
