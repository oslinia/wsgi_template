import unittest
from io import BytesIO

from framework.http import Query, Cookie, Form

from .test_request import request_tests
from .test_response import response_tests


class TestModule(unittest.TestCase):
    def test_http(self):
        query = Query({'QUERY_STRING': 'query=one&append=two'})

        self.assertTupleEqual(('one', 'two'), (query.get('query'), query['append']))

        cookie = Cookie({'HTTP_COOKIE': 'cookie=one; append=two'})

        self.assertTupleEqual(('one', 'two'), (cookie.get('cookie'), cookie['append']))

        form = Form({
            'CONTENT_TYPE': 'application/x-www-form-urlencoded',
            'wsgi.input': BytesIO(b'form=one&append=two'),
        })

        self.assertTupleEqual(('one', 'two'), (form.data.get('form'), form.data['append']))

        form = Form({
            'CONTENT_TYPE': 'multipart/form-data; boundary=----TestBoundarySeparator',
            'wsgi.input': BytesIO(b'------TestBoundarySeparator\r\n'
                                  b'Content-Disposition: form-data; name="files"; filename="file.txt"\r\n'
                                  b'Content-Type: text/plain\r\n'
                                  b'\r\n'
                                  b'simple text\r\n'
                                  b'------TestBoundarySeparator\r\n'
                                  b'Content-Disposition: form-data; name="description"\r\n'
                                  b'\r\n'
                                  b'description\r\n'
                                  b'------TestBoundarySeparator--\r\n')
        })

        self.assertTupleEqual(
            ('description', {'file.txt': {'type': 'text/plain', 'body': b'simple text'}}),
            (form.data['description'], form.files['files'])
        )


def http_tests():
    suite = unittest.TestSuite()

    for test in (
            'test_http',
    ):
        suite.addTest(TestModule(test))

    suite.addTests(request_tests())
    suite.addTests(response_tests())

    return suite
