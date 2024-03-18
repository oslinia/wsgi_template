import mimetypes
import os
import sys
from collections.abc import Callable, Generator
from typing import Any

from . import Map
from .map import Link, Pattern, Callback
from ..alias import HeadersAlias, StartResponse, WSGIEnvironment, WSGIGenerator
from ..http import request, response, Query, Cookie, Form
from ..http.response.header import Header
from ..http.response.template import Template

status_codes = {
    200: '200 OK',
    301: '301 Moved Permanently',
    302: '302 Moved Temporarily',
    307: '307 Temporary Redirect',
    308: '308 Permanent Redirect',
    403: '403 Forbidden',
    404: '404 Not Found',
    500: '500 Internal Server Error',
    520: '520 Unknown Error',
}


def status(code: int):
    return status_codes[code if code in status_codes.keys() else 520]


class Kernel(object):
    __slots__ = ('encoding', 'buffer_size', 'size', 'headers', 'mimetype')

    encoding: str
    buffer_size: int
    size: int
    headers: HeadersAlias
    mimetype: str

    def mime(self, mimetype: str | None, encoding: str | None):
        if mimetype is None:
            mimetype = 'text/plain'

        if mimetype.startswith('text/'):
            if 0 < self.size:
                if encoding is None:
                    encoding = self.encoding

                mimetype = f"{mimetype}; charset={encoding}"

        self.mimetype = mimetype

    def content_header(self, mimetype: str):
        self.headers.extend([('content-length', str(self.size)), ('content-type', mimetype)])

        return self.headers


class File(Kernel):
    __slots__ = ('file',)

    def __init__(self, file: str):
        self.file, self.size, self.headers = file, os.path.getsize(file), HeadersAlias()

        self.mime(*mimetypes.guess_type(file, strict=True))

    def __call__(self, start_response: StartResponse) -> Generator[bytes]:
        start_response(status(200), self.content_header(self.mimetype))

        try:
            f = open(self.file, 'rb')
            for i in range(0, self.size, self.buffer_size):
                yield f.read(self.buffer_size)

            f.close()

        except OSError:
            pass


class Body(Kernel):
    __slots__ = ('body', 'code')

    def __init__(
            self,
            body: Any,
            code: int = None,
            headers: HeadersAlias = None,
            mimetype: str = None,
            encoding: str = None,
    ):
        if not isinstance(body, bytes):
            if isinstance(body, str):
                body = body.encode(encoding := self.encoding if encoding is None else encoding)

            else:
                body = b''

        self.size = len(body)

        if code is None:
            code = 200

        if headers is None:
            headers = HeadersAlias()

        header: Header = getattr(response, '_header')

        headers.extend(header.headers())
        headers.extend(header.cookies())

        self.mime(mimetype, encoding)

        self.body, self.code, self.headers = body, code, headers

    def __call__(self, start_response: StartResponse) -> Generator[bytes]:
        start_response(status(self.code), self.content_header(self.mimetype))

        for i in range(0, self.size, self.buffer_size):
            yield self.body[i:i + self.buffer_size]


class Static(object):
    __slots__ = ('isdir', 'folder', 'urlpath', 'filepath')

    filepath: str

    def __init__(self, folder: str, urlpath: str):
        self.isdir = os.path.isdir(folder)

        if self.isdir:
            self.folder, self.urlpath = folder, urlpath

    def isfile(self, environ: WSGIEnvironment):
        if self.isdir:
            path_info = environ['PATH_INFO']

            if path_info.startswith(self.urlpath):
                self.filepath: str = os.path.join(self.folder, path_info[len(self.urlpath):])

                return os.path.isfile(self.filepath)

    @property
    def file(self) -> WSGIGenerator:
        return File(self.filepath)


def import_call(module: str, name: str, method: str | None) -> Callable[..., Any]:
    __import__(module)

    call = getattr(sys.modules[module], name)

    if method is not None:
        call = getattr(call(), method)

    return call


def as_tuple(call: Any):
    return call if isinstance(call, tuple) else (call,)


class Router(object):
    __slots__ = ('pattern', 'callback', 'import_error', 'generator')

    generator: WSGIGenerator

    def __init__(
            self,
            urlmap: Map,
            import_error: tuple[str, str, str | None] | None,
            static_urlpath: str,
            template_folder: str,
    ):
        self.pattern, self.callback = Pattern(urlmap), Callback(urlmap)

        if import_error is not None:
            self.import_error = import_error

        for attr, value in (('_static', static_urlpath), ('_link', Link(urlmap))):
            setattr(response, attr, value)

        setattr(Template, 'templates', template_folder)

    def __call__(self, environ: WSGIEnvironment) -> WSGIGenerator:
        link, kwargs = self.request(environ)

        if link is None:
            self.error(404)

        else:
            self.router(link, kwargs)

        return self.generator

    def request(self, environ: WSGIEnvironment):
        for attr, value in (
                ('_env', environ),
                ('_query', Query(environ)),
                ('_cookie', Cookie(environ)),
                ('_form', Form(environ)),
        ):
            setattr(request, attr, value)

        setattr(response, '_header', Header())

        return self.pattern.parse(environ)

    def error(self, code: int):
        if hasattr(self, 'import_error'):
            self.generator = Body(*as_tuple(import_call(*self.import_error)(code)))

        else:
            message = {
                404: 'Not Found',
                500: 'Internal Server Error',
            }

            self.generator = Body(message[code], code, None, 'text/plain', 'ascii')

    def router(self, link: str, kwargs: dict[str, Any]):
        module, name, method, args = self.callback[link]

        self.generator = Body(*as_tuple(import_call(module, name, method)(*args, **kwargs)))
