# Define exceptions for telegram chat-bot application

class Err(Exception):
    '''Base class for other user-defined exceptions
    '''
    pass

class MaximumUsersNumberReached(Err):
    '''
    Raises when new user tries to connect when the maximum number of the users is reached.
    '''
    def __init__(self, max_users_number:int, delay: float):
        msg = f'The maximum number of the users ({max_users_number}) is reached.\n'
        msg += f'Try again in {delay} minutes'
        self.msg = msg

    def __str__(self):
        return self.msg

#########################################################

class MenuEntryLevelError(Err):
    '''Raises when the application can not correctly parse a level
    of menu entry passed to menu constructor.
    '''

    def __init__(self, lvl: str):
        msg: str = '''The first line of each menu entry must begin \
 from its hierarchical level represented by digits and periods, \
 and be separated from the rest of the line by a space .'''
        self.lvl = lvl
        self.msg = msg
        super().__init__(self.msg)

    def __str__(self):
        return f'{self.lvl} -> {self.msg}'


class DuplicateMenuEntryError(Err):
    '''
    Raises when a menu entry of the same level has been added to the menu earlier
    '''

    def __init__(self, lvl: str):
        self.lvl: str = lvl
        self.msg: str = f'A menu entry of the same level {self.lvl} has been added earlier.'
        super().__init__(self.msg)

    def __str__(self):
        return self.msg


class ConfigurationParametersError(Err):
    '''
    Raises if configuration parameters such as bot TOKEN and OWNER_ID cannot be loaded
    from environmental variables
    '''

    def __init__(self, absent_values: dict):
        self.msg: str = f'Cannot establish one or more of these parameters: {absent_values}'
        super().__init__(self.msg)

    def __str__(self):
        return self.msg
