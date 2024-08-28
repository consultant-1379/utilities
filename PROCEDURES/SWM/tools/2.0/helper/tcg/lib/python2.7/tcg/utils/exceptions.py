'''
All the tcg related exceptions should be created here
'''


class TcgException(Exception):  # pylint: disable-msg=C0111
    '''
    This is the most generic type of exception in tcg
    '''
    def __init__(self, value):
        Exception.__init__(self, value)
        self.__value = value

    def __str__(self):
        return repr(self.__value)
