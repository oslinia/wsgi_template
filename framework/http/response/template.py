import os
import re


class Http(object):
    __slots__ = ('_request', '_response')

    def __init__(self):
        from .. import request, response

        self._request, self._response = request, response

    def url_file(self, name: str):
        return self._response.url_file(name.strip(r'\'"'))

    def url_for(self, args_kwargs: str):
        args, kwargs = list(), dict()

        for item in args_kwargs.split(','):
            if '=' in item:
                k, v = item.lstrip().split('=')

                kwargs.update({k: v.strip(r'\'"')})

            else:
                args.append(item.strip(r'\'"'))

        url = self._response.url_for(*args, **kwargs)

        return str(url) if url is None else url

    def form(self, name: str):
        value = self._request.form(name.strip(r'\'"'))

        return '' if value is None else value


def context_replace(context: dict[str, str] | None, body: str):
    keys, http = tuple() if context is None else context.keys(), Http()

    for key in re.findall(r'{{ ([A-Za-z0-9_]+\(?[\sA-Za-z0-9_,=\'."]*\)?) }}', body):
        if key in keys:
            body = body.replace('{{ %s }}' % key, context[key])

        elif '(' in key:
            if r := re.findall(r'([A-Za-z0-9_]+)\(\s*([A-Za-z0-9 _,=\'."]+[\'"])', key):
                name, args = r[-1]

                if name not in http.__slots__ and hasattr(http, name):
                    body = body.replace('{{ %s }}' % key, getattr(http, name)(args))

    return body.rstrip()


def endings_list(end_blocks: list[str], line: str):
    endings = list()

    for end_block in end_blocks:
        part, line = re.split(end_block, line, 1)

        if end_block.startswith('{%-'):
            part = part.rstrip()

        endings.append(part)

    endings.append(line)

    return endings


class Frame(object):
    __slots__ = ('templates', 'block', 'body')

    block: dict[str, str]
    body: str

    def __init__(self, templates: str):
        self.templates = templates

    def get_body(self, filename: str | os.PathLike):
        filepath = os.path.abspath(os.path.join(self.templates, filename))

        if os.path.isfile(filepath):
            body_tuples = self.body_tuples(filepath, list())

            if body_tuples:
                self.body, self.block = '', dict()

                for tuples in body_tuples:
                    self.tuple_handler(tuples)

            else:
                return 'Error reading file.'

            for k, v in self.block.items():
                self.body = re.sub(f"{{% {k} %}}", v, self.body)

            return self.body

    def body_tuples(self, filepath: str, lists: list[list[tuple[str | None, str]]]):
        try:
            f = open(filepath, 'r')
            body = f.read()
            f.close()

            if extend := re.search(r'^(.*)({% extends [\'"][A-Za-z0-9_/.]+[\'"] %})(.*)(\s+)', body):
                body = re.sub(''.join(extend.groups()), '', body)

                if os.path.isfile(filepath := os.path.join(
                        self.templates, re.search(r'(?<=[\'"]).*(?=[\'"])', extend.group(2)).group()
                )):
                    lists = self.body_tuples(filepath, lists)

            if blocks := re.findall(r'({% block [A-Za-z0-9_]+ -*%})', body):
                items, prev = list(), None

                for block in blocks:
                    value, body = re.split(block, body, 1)

                    items.append((prev, value))

                    prev = block

                    if block.endswith('-%}'):
                        body = body.lstrip()

                items.append((prev, body))

            else:
                items = [(None, body)]

            lists.append(items)

            return lists

        except OSError:
            pass

    def tuple_handler(self, tuples: list[tuple[str | None, str]]):
        body, depth = list(), list()

        for block, line in tuples:
            if block is None:
                body.append(line)

            else:
                name = re.search(r'(?<= block )([A-Za-z0-9_]+)', block).group()
                key = name not in self.block.keys()

                if ' endblock %}' in line and (end_blocks := re.findall(r'({%-* endblock %})', line)):
                    body, depth, key = self.end_block(name, endings_list(end_blocks, line), depth, key, body)

                else:
                    depth.append(name)

                    if key:
                        body.append(f"{{% {name} %}}")

                    self.block[name] = self.add_super(name, line)

        self.body = f"{self.body}{''.join(body).rstrip()}"

    def end_block(self, name: str, endings: list[str], depth: list[str], key: bool, body: list[str]):
        self.block[name], i = self.add_super(name, endings.pop(0)), 0

        for ending in endings:
            if depth:
                current = depth.pop()

                if 0 == i:
                    if key:
                        ending, key = f"{{% {name} %}}{ending}", False

                else:
                    if current not in self.block.keys():
                        ending = f"{{% {current} %}}{ending}"

                self.block[current] = self.add_super(name, f"{self.block[current]}{ending}")

            else:
                if key:
                    body.append(f"{{% {name} %}}{ending}")

                else:
                    body.append(ending)

            i += 1

        return body, depth, key

    def add_super(self, name: str, line: str):
        if '{{ super() }}' in line:
            if name in self.block.keys():
                return re.sub(r'{{ super\(\) }}', self.block[name].rstrip(), line)

        return line


class Template(object):
    __slots__ = ('templates', 'body')

    templates: str
    body: str | None

    def __init__(self, filename: str | os.PathLike):
        self.body = Frame(self.templates).get_body(filename)

    def render(self, context: dict[str, str] | None):
        if self.body is None:
            return b'Template file not found.'

        else:
            return context_replace(context, self.body)
