# Define exceptions for telegram chatbot application
from __future__ import annotations


class Err(Exception):
    """Base class for other user-defined exceptions
    """
    pass


class MaximumUsersNumberReached(Err):
    """
    Raises when new user tries to connect when the maximum number of the users is reached.
    """
    def __init__(self, max_users_number:int, delay: float | str):
        msg = f'The maximum number of the users ({max_users_number}) is reached.\n'
        msg += f'Try again in {delay} minutes'
        self.msg = msg

    def __str__(self):
        return self.msg