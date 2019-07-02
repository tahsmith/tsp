import os
import re
import io

from hypothesis import (
    given,
    assume
)

import hypothesis.strategies as st

from tsp import (
    re_format,
    file_or_open,
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
def test_file_or_open_exists(s, text, mode, tmpdir):
    binary = isinstance(text, bytes)
    if not binary:
        assert isinstance(text, str)
        assume('\r' not in text)

    path = str(tmpdir / s)
    assert True
    if mode != 'w':
        with open(path, 'w' + ('b' if binary else '')) as f:
            f.write(text)
    if binary:
        assume(mode)
        mode += 'b'

    default_mode = mode or 'r'

    with file_or_open(path, mode) as f:
        if 'b' in default_mode:
            assert isinstance(f, io.BufferedIOBase)
        else:
            assert isinstance(f, io.TextIOBase)

        if 'w' in default_mode:
            f.write(text)
        else:
            assert 'r' in default_mode
            assert text == f.read()

    os.path.exists(path)

    with open(path, 'r' + ('b' if binary else '')) as f:
        assert text == f.read()
