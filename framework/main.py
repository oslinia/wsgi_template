import io
import os
import sys
from collections.abc import Callable, Iterable

from .alias import StartResponse, WSGIEnvironment, WSGIApplication
from .routing import Map
from .routing.kernel import Kernel, Static, Router


def valid_static(urlpath: str | None):
    if urlpath is None:
        return '/static/'

    if not urlpath.startswith('/'):
        raise ValueError(
            "URL for static files must begin with a slash: '%s'" % urlpath
        )

    if not urlpath.endswith('/'):
        raise ValueError(
            "URL for static files must end with a slash: '%s'" % urlpath
        )

    return urlpath


def absolute_path(dirname: str, path: str | None, default: str):
    if path is None:
        path = default

    return os.path.abspath(os.path.join(dirname, path))


def as_import(error_handler: Callable | tuple[Callable] | tuple[Callable, str] | None):
    if error_handler is not None:
        if isinstance(e := error_handler, tuple):
            error_handler, method = e[0], e[1] if 2 == len(e) else '__call__'

        else:
            method = '__call__' if isinstance(error_handler, type) else None

        return error_handler.__module__, error_handler.__name__, method


class Main(object):
    __slots__ = ('static', 'router')

    def __init__(
            self: WSGIApplication,
            import_name: str,
            urlmap: Map,
            error_handler: Callable | tuple[Callable] | tuple[Callable, str] = None,
            static_urlpath: str = None,
            static_folder: str | os.PathLike = None,
            template_folder: str | os.PathLike = None,
    ):
        dirname = os.path.dirname(sys.modules[import_name].__file__)

        self.static = Static(
            absolute_path(dirname, static_folder, 'static'),
            static_urlpath := valid_static(static_urlpath),
        )

        self.router = Router(
            urlmap,
            as_import(error_handler),
            static_urlpath,
            absolute_path(dirname, template_folder, 'templates'),
        )

        for attr, value in (('encoding', 'utf-8'), ('buffer_size', io.DEFAULT_BUFFER_SIZE)):
            setattr(Kernel, attr, value)

    def __call__(self, environ: WSGIEnvironment, start_response: StartResponse) -> Iterable[bytes]:
        if self.static.isfile(environ):
            return self.static.file(start_response)

        return self.router(environ)(start_response)
