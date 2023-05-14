import io
import os
import re

import hypothesis.strategies as st
import pytest
from hypothesis import (
    given,
    assume
)

from tsp import (
    re_format,
    file_or_open,
    absent_if_none,
    pack_args,
    call_packed
)


def st_any():
    x = st.deferred(
        lambda: st_hashable()
                | st.lists(x)
                | st.dictionaries(st_hashable(), x)
                | st.sets(st_hashable())
    )
    return x


def st_hashable():
    x = st.deferred(
        lambda: st.text()
                | st.binary()
                | st.integers()
                | st.floats(allow_nan=False)
                | st.decimals(allow_nan=False)
                | st.fractions()
                | st.datetimes()
                | st.tuples(x)
                | st.frozensets(x)

    )

    return x


@given(st_any() | st.just(r'\s$^.*'))
def test_re_format(obj):
    assert re.match(rf'^{re_format(obj)}$', f'{obj}')


@given(s=st.just('x'),
       text=st.text()
            | st.binary(),
       mode=st.just(None)
            | st.just('w')
            | st.just('r'))
def test_file_or_open_file_exists(s, text, mode, tmpdir):
    binary = isinstance(text, bytes)
    if not binary:
        assert isinstance(text, str)
        assume('\r' not in text)

    path = str(tmpdir / s)
    try:
        os.remove(path)
    except FileNotFoundError:
        pass

    if mode != 'w':
        with open(path, 'w' + ('b' if binary else '')) as f:
            f.write(text)
    if binary:
        assume(mode)
        mode += 'b'

    with file_or_open(path, **absent_if_none(mode=mode)) as f:
        if mode and 'b' in mode:
            assert isinstance(f, io.BufferedIOBase)
        else:
            assert isinstance(f, io.TextIOBase)

        if mode and 'w' in mode:
            f.write(text)
        else:
            assert mode is None or 'r' in mode
            assert text == f.read()

    os.path.exists(path)

    with open(path, 'r' + ('b' if binary else '')) as f:
        assert text == f.read()


@given(s=st.just('x'),
       text=st.text()
            | st.binary(),
       mode=st.just(None)
            | st.just('w')
            | st.just('r'))
def test_file_or_open_file_absent(s, text, mode, tmpdir):
    binary = isinstance(text, bytes)
    if not binary:
        assert isinstance(text, str)
        assume('\r' not in text)

    path = str(tmpdir / s)
    try:
        os.remove(path)
    except FileNotFoundError:
        pass

    if binary:
        assume(mode)
        mode += 'b'

    try:
        with file_or_open(path, **absent_if_none(mode=mode)) as f:
            if mode and 'b' in mode:
                assert isinstance(f, io.BufferedIOBase)
            else:
                assert isinstance(f, io.TextIOBase)
            if mode and 'w' in mode:
                f.write(text)
            else:
                pytest.fail('Should have raised a FileNotFoundError')
    except Exception as e:
        if mode is None or 'r' in mode:
            assert isinstance(e, FileNotFoundError)
        else:
            pytest.fail('unexpected exception')

    if mode and 'w' in mode:
        with open(path, 'r' + ('b' if binary else '')) as f:
            assert text == f.read()


@given(args=st.tuples(st_any()), kwargs=st.dictionaries(st.text(), st_any()))
def test_pack_args(args, kwargs):
    packed = pack_args(*args, **kwargs)
    assert packed['args'] == args
    assert packed['kwargs'] == kwargs


@given(args=st.tuples(st_any()), kwargs=st.dictionaries(st.text(), st_any()))
def test_call_packed(args, kwargs):
    call_count = 0

    def f(*actual_args, **actual_kwargs):
        nonlocal call_count
        call_count += 1
        assert actual_args == args
        assert actual_kwargs == kwargs

    call_packed(f, args, kwargs)
    assert call_count == 1
