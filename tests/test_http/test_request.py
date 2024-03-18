import unittest
from io import BytesIO

from framework.http.request import env, query, cookie, form, upload, Path
from framework.main import Main
from framework.routing import Map

from .. import dummy_environ, DummyStartResponse

environ, start_response = dummy_environ.copy(), DummyStartResponse()


class TestModule(unittest.TestCase):
    def test_environ(self):
        app = Main(__name__, Map(()))

        environ['PATH_INFO'] = '/'

        list(app(environ, start_response))

        self.assertEqual('/', env('PATH_INFO'))
        self.assertIsNone(query('query'))
        self.assertIsNone(cookie('cookie'))
        self.assertIsNone(form('form'))
        self.assertIsNone(upload('upload'))

        environ['PATH_INFO'] = '/path_info'
        environ['QUERY_STRING'] = 'query=one&append=two'
        environ['HTTP_COOKIE'] = 'cookie=one; append=two'
        environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'
        environ['wsgi.input'] = BytesIO(b'form=one&append=two')

        list(app(environ, start_response))

        self.assertEqual('/path_info', env('PATH_INFO'))
        self.assertTupleEqual(('one', 'two'), (query('query'), query('append')))
        self.assertTupleEqual(('one', 'two'), (cookie('cookie'), cookie('append')))
        self.assertTupleEqual(('one', 'two'), (form('form'), form('append')))

        environ['CONTENT_TYPE'] = 'multipart/form-data; boundary=----TestBoundarySeparator'
        environ['wsgi.input'] = BytesIO(b'------TestBoundarySeparator\r\n'
                                        b'Content-Disposition: form-data; name="files"; filename="file.txt"\r\n'
                                        b'Content-Type: text/plain\r\n'
                                        b'\r\n'
                                        b'simple text\r\n'
                                        b'------TestBoundarySeparator\r\n'
                                        b'Content-Disposition: form-data; name="description"\r\n'
                                        b'\r\n'
                                        b'description\r\n'
                                        b'------TestBoundarySeparator--\r\n')

        list(app(environ, start_response))

        self.assertTupleEqual(
            ('description', {'file.txt': {'type': 'text/plain', 'body': b'simple text'}}),
            (form('description'), upload('files'))
        )

    def test_path(self):
        path = Path({'str': 'str', 'int': 1, 'float': 0.1})

        self.assertEqual("{'str': 'str', 'int': 1, 'float': 0.1}", str(path))
        self.assertEqual('str', path.get('str'))
        self.assertEqual(1, path['int'])
        self.assertEqual(0.1, path['float'])


def request_tests():
    suite = unittest.TestSuite()

    for test in (
            'test_environ',
            'test_path',
    ):
        suite.addTest(TestModule(test))

    return suite
