import inspect
from . import main


def test(*args, **kwargs):
    if 'wrapper' in kwargs:
        t = kwargs['wrapper']()
    else:
        t = main.TestWrapper()

    if '_builtin' in kwargs:
        t.builtin = kwargs['_builtin']

    def wrapper(func):
        t.name = func.__name__
        t.args = inspect.getfullargspec(func).args
        t.func = func

        def inner(*a, **kw):
            return t(*a, **kw)

        if t.name is not None:
            main.tasks[t.name] = t
        return inner

    return wrapper


def http_test(*args, **kwargs):
    from .http import HttpWrapper
    t = HttpWrapper()

    if '_builtin' in kwargs:
        t.builtin = kwargs['_builtin']

    def wrapper(func):
        t.name = func.__name__
        t.args = inspect.getfullargspec(func).args
        t.func = func

        def inner(*a, **kw):
            return t(*a, **kw)

        main.tasks[t.name] = t
        return inner

    return wrapper


