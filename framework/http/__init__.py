import re
from urllib.parse import unquote

from ..alias import WSGIEnvironment


class Query(dict[str, str]):
    def __init__(self, environ: WSGIEnvironment):
        dict.__init__(self)

        for key, value in (
                ((p := i.split('=', 1))[0], p[1] if 1 < len(p) else '')
                for i in environ['QUERY_STRING'].split('&')
        ):
            self[key] = value


class Cookie(dict[str, str]):
    def __init__(self, environ: WSGIEnvironment):
        dict.__init__(self)

        if 'HTTP_COOKIE' in environ:
            for key, value in (
                    ((p := i.split('='))[0], p[1])
                    for i in environ['HTTP_COOKIE'].split('; ')
            ):
                self[key] = value


class Form(object):
    __slots__ = ('data', 'files', 'boundary')

    def __init__(self, environ: WSGIEnvironment):
        self.data: dict[str, str] = dict()
        self.files: dict[str, dict[str, dict[str, str | bytes]]] = dict()

        if 'CONTENT_TYPE' in environ:
            content = environ['CONTENT_TYPE'].split('; ')

            if 1 == len(content):
                self.boundary = None

            else:
                self.boundary: bytes = content[1].split('=')[1].encode('ascii')

            if hasattr(self, method := content[0].split('/')[0]):
                getattr(self, method)(environ)

    def application(self, environ: WSGIEnvironment):
        if '' != (string := unquote(environ['wsgi.input'].read().decode('utf-8'))):
            for key, value in (
                    ((p := i.split('=', 1))[0], p[1] if 1 < len(p) else '')
                    for i in string.split('&')
            ):
                self.data[key] = value

    def multipart(self, environ: WSGIEnvironment):
        i, d, name, filename, not_empty = 0, -1, None, None, False

        for line in environ['wsgi.input'].readlines():
            if 45 == line[0]:
                if self.boundary in line:
                    if name is not None:
                        if name in self.data.keys():
                            self.data[name] = re.sub(r'\r\n$', '', self.data[name])

                        elif name in self.files.keys():
                            file = self.files[name].get(filename)

                            if file is not None:
                                self.files[name][filename]['body'] = re.sub(b'\\r\\n$', b'', file['body'])

                    d, name, filename, not_empty = i + 1, None, None, False

            if i == d:
                if line.startswith(b'Content-Disposition'):
                    d, items = i + 1, re.sub(b'\\r\\n$', b'', line).split(b'; ')[1:]

                    if 1 == len(items):
                        name = items[0].decode('ascii').split('=')[1].strip('"')

                        self.data[name] = ''

                    else:
                        for item in items:
                            key, value = (s := item.decode('ascii').split('='))[0], s[1].strip('"')

                            match key:
                                case 'name':
                                    name = value

                                    if name not in self.files.keys():
                                        self.files[name] = dict()

                                case 'filename':
                                    filename = value

                                    if not_empty := '' != filename:
                                        self.files[name][filename] = {'type': None, 'body': b''}

                if line.startswith(b'Content-Type'):
                    d, line = i + 1, re.sub(b'\\r\\n$', b'', line)

                    if filename in self.files[name].keys():
                        self.files[name][filename]['type'] = line.decode('ascii').split(': ')[1]

            elif name is not None:
                if filename is None:
                    self.data[name] += line.decode('utf-8')

                elif not_empty:
                    self.files[name][filename]['body'] += line

            i += 1
