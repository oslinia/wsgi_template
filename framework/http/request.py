from . import Query, Cookie, Form
from ..alias import WSGIEnvironment

_env: WSGIEnvironment
_query: Query
_cookie: Cookie
_form: Form


def env(name: str):
    return _env.get(name)


def query(name: str):
    return _query.get(name)


def cookie(name: str):
    return _cookie.get(name)


def form(name: str):
    return _form.data.get(name)


def upload(name: str):
    return _form.files.get(name)


class Path(object):
    __slots__ = ('_dict',)

    def __init__(self, tokens: dict[str, str | int | float]):
        self._dict = tokens

    def __getitem__(self, key: str):
        return self._dict[key]

    def __repr__(self):
        return self._dict.__repr__()

    def get(self, key: str):
        return self._dict.get(key)
