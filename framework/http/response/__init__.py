import os
from datetime import datetime, timedelta
from typing import Literal

from .header import Cookie, Header
from .template import Template
from ...routing.map import Link

_static: str
_link: Link
_header: Header


def url_file(name: str):
    return f"{_static}{name}"


def url_for(*args: str, **kwargs: str):
    return _link.collect(args, kwargs)


def set_header(name: str, value: str):
    _header.simple[name.lower()] = value


def get_header(name: str):
    return _header.simple.get(name.lower())


def has_header(name: str):
    return name.lower() in _header.simple.keys()


def delete_header(name: str):
    if (name := name.lower()) in _header.simple.keys():
        del _header.simple[name]


def set_cookie(
        name: str,
        value: str,
        expires: datetime | str | int | float = None,
        max_age: timedelta | int = None,
        path: str = '/',
        domain: str = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: Literal['none', 'lax', 'strict'] = None,
):
    cookie = Cookie(name, value)

    if expires is not None:
        cookie['expires'] = expires

    if max_age is not None:
        cookie['max-age'] = max_age

    cookie['path'] = path

    if domain is not None:
        cookie['domain'] = domain

    if secure:
        cookie['secure'] = 'Secure'

    if httponly:
        cookie['httponly'] = 'HttpOnly'

    if samesite is not None:
        cookie['samesite'] = samesite

    _header.cookie[name] = cookie.value


def delete_cookie(name: str, path: str = '/', domain: str = None):
    cookie = Cookie(name, '')

    cookie['expires'] = 0

    cookie['path'] = path

    if domain is not None:
        cookie['domain'] = domain

    _header.cookie[name] = cookie.value


def redirect_page(urlpath: str, status_code: int = 307):
    return b'', status_code, [('location', urlpath)]


def render_template(filename: str | os.PathLike, context: dict[str, str] = None, status_code: int = None):
    return Template(filename).render(context), status_code, None, 'text/html'
