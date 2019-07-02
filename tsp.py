import re
import pickle
import typing
from contextlib import contextmanager
from functools import wraps
import typing as ty

FileOrPath = ty.Union[ty.AnyStr, ty.IO]


def dump_iterable(f: FileOrPath, iterable: ty.Iterable):
    for x in iterable:
        pickle.dump(x, f)


def load_iterable(f: FileOrPath):
    with file_or_open(f, 'rb') as f:
        while True:
            try:
                yield pickle.load(f)
            except EOFError:
                break


def dumpf(f: FileOrPath, obj: ty.Any):
    with file_or_open(f, 'wb') as f:
        pickle.dump(obj, f)


def loadf(f: FileOrPath):
    with file_or_open(f, 'rb') as f:
        return pickle.load(f)


@contextmanager
def file_or_open(f: FileOrPath, mode: ty.AnyStr = None):
    if isinstance(f, str):
        kwargs = {}
        if mode is not None:
            kwargs['mode'] = mode
        f = open(f, **kwargs)
        close = True
    elif isinstance(f, typing.IO):
        close = False
    else:
        raise ValueError('f must be a string of a file like object. Got {type}'
                         .format(type=type(f)))

    try:
        yield f
    finally:
        if close:
            f.close()


def re_format(x: ty.Any):
    return ReEscapeWrapper(x)


class ReEscapeWrapper(ty.NamedTuple):
    obj: ty.Any

    def __format__(self, format_spec):
        return re.escape(self.obj.__format__(format_spec))


def returning_generator(gen: ty.Callable):
    @wraps(gen)
    def f(*args, **kwargs):
        return ReturningGenerator(gen(*args, **kwargs))

    return f


class ReturningGenerator:

    def __init__(self, gen):
        self.gen = gen

    def __iter__(self):
        self.result = yield from self.gen


def as_args(*args, **kwargs):
    return args, kwargs


def absent_if_none(**kwargs):
    return {k: v for k, v in kwargs.items() if v is not None}
