import os
import re
import io

import pytest
from hypothesis import (
    given,
    assume
)

import hypothesis.strategies as st

from tsp import (
    re_format,
    file_or_open,
    absent_if_none
)


def st_any():
    x = st.deferred(
        lambda: st.text()
                | st.binary()
                | st.integers()
                | st.floats()
                | st.lists(x)
                | st.dictionaries(st.text(), x)
                | st.sets(st.text())
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
