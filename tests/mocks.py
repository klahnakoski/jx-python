from mo_logs import logger


def mockable(enable):
    """
    FUNCTION DECORATOR TO ALLOW MOCKING THIS FUNCTION
    :param enable:
    :return:
    """
    if isinstance(enable, bool):

        def decorator(func):
            if enable:
                return Mockable(func)
            else:
                return func

        return decorator

    # ALLOW FUNCTION TO BE CALLED AS A DECORATOR
    return Mockable(enable)


class Mockable:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


def mock(target, child=None, *, value=None, function=None):
    """
    FUNCTION DECORATOR TO ALLOW REPLACEMENT WITH ANOTHER function (OR value)
    """
    if child:
        please_mock = getattr(target, child)
        if not isinstance(please_mock, Mockable):
            please_mock = mockable(True)(please_mock)
        setattr(target, child, please_mock)
        target = please_mock

    if function is None:
        function = _constant(value)

    return Mocking(target, function)


class Mocking:
    """
    REPLACE mockable WITH mock FOR THE DURATION OF THIS CONTEXT
    """

    def __init__(self, mockable, mock):
        if not isinstance(mockable, Mockable):
            logger.error("expecting Mockable, not {mockable}", mockable=mockable, stack_depth=1)
        self.mockable = mockable
        self.mock = mock
        self.func = None

    def __enter__(self):
        self.func, self.mockable.func = self.mockable.func, self.mock

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.func, self.mockable.func = None, self.func

    def __call__(self, func):
        def wrapped(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return wrapped


def _constant(value):
    def f(*args, **kwargs):
        return value

    return f
