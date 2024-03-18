import json
import os
import shutil
import unittest

from framework.http.request import Path
from framework.main import Main
from framework.routing import Rule, Endpoint, Map

from .. import dummy_environ, DummyStartResponse

environ, start_response = dummy_environ.copy(), DummyStartResponse()


def dummy_status(path: Path):
    return b'', path['status']


class TestModule(unittest.TestCase):
    def test_default(self):
        static_folder = os.path.join(os.path.dirname(__file__), 'static')

        if os.path.isdir(static_folder):
            shutil.rmtree(static_folder)

        app = Main(__name__, Map(()))

        self.assertFalse(app.static.isdir)

        with self.assertRaises(AttributeError):
            getattr(app.static, 'folder')

        with self.assertRaises(AttributeError):
            getattr(app.static, 'urlpath')

        with self.assertRaises(AttributeError):
            getattr(app.static, 'filepath')

        environ['PATH_INFO'] = '/'

        self.assertEqual(b'Not Found', b''.join(app(environ, start_response)))
        self.assertEqual('404 Not Found', start_response.status)
        for key, value in start_response.headers:
            match key:
                case 'content-length':
                    self.assertEqual('9', value)

                case 'content-type':
                    self.assertEqual('text/plain; charset=ascii', value)

        os.mkdir(static_folder)

        app = Main(__name__, Map(()))

        self.assertTrue(app.static.isdir)
        self.assertEqual(static_folder, app.static.folder)
        self.assertEqual('/static/', app.static.urlpath)

        with self.assertRaises(AttributeError):
            getattr(app.static, 'filepath')

        filepath = os.path.join(static_folder, 'test.file')

        with open(filepath, 'w') as f:
            f.write('simple text')

        environ['PATH_INFO'] = '/static/test.file'

        self.assertEqual(b'simple text', b''.join(app(environ, start_response)))
        self.assertEqual(filepath, app.static.filepath)
        self.assertEqual('200 OK', start_response.status)
        for key, value in start_response.headers:
            match key:
                case 'content-length':
                    self.assertEqual('11', value)

                case 'content-type':
                    self.assertEqual('text/plain; charset=utf-8', value)

    def test_args(self):
        app = Main(__name__, Map(()), static_urlpath='/folder/')

        environ['PATH_INFO'] = '/folder/test.file'

        self.assertEqual(b'simple text', b''.join(app(environ, start_response)))

        static_folder = os.path.join(os.path.dirname(__file__), 'folder', 'path', 'to')

        app = Main(__name__, Map(()), static_urlpath='/', static_folder=static_folder)

        self.assertTrue(app.static.isdir)
        self.assertEqual(static_folder, app.static.folder)
        self.assertEqual('/', app.static.urlpath)

        environ['PATH_INFO'] = '/test.json'

        self.assertDictEqual({'bool': True}, json.loads(b''.join(app(environ, start_response))))
        self.assertEqual(os.path.join(static_folder, 'test.json'), app.static.filepath)
        self.assertEqual('200 OK', start_response.status)
        for key, value in start_response.headers:
            match key:
                case 'content-length':
                    self.assertEqual('20', value)

                case 'content-type':
                    self.assertEqual('application/json', value)

        with self.assertRaises(ValueError) as context:
            Main(__name__, Map(()), static_urlpath='/urlpath')

        self.assertEqual(
            "URL for static files must end with a slash: '/urlpath'",
            context.exception.args[0],
        )

        with self.assertRaises(ValueError) as context:
            Main(__name__, Map(()), static_urlpath='urlpath/')

        self.assertEqual(
            "URL for static files must begin with a slash: 'urlpath/'",
            context.exception.args[0],
        )

    def test_status(self):
        def status(code: int):
            environ['PATH_INFO'] = f"/{code}"
            list(app(environ, start_response))

            return start_response.status

        app = Main(__name__, Map((
            Rule('/<int:status>', 'status'),
            Endpoint('status', dummy_status)
        )))

        self.assertEqual('200 OK', status(200))
        self.assertEqual('301 Moved Permanently', status(301))
        self.assertEqual('302 Moved Temporarily', status(302))
        self.assertEqual('307 Temporary Redirect', status(307))
        self.assertEqual('308 Permanent Redirect', status(308))
        self.assertEqual('403 Forbidden', status(403))
        self.assertEqual('404 Not Found', status(404))
        self.assertEqual('500 Internal Server Error', status(500))
        self.assertEqual('520 Unknown Error', status(520))


def main_tests():
    suite = unittest.TestSuite()

    for test in (
            'test_default',
            'test_args',
            'test_status',
    ):
        suite.addTest(TestModule(test))

    return suite
