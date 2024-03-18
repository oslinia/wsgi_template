import unittest

from framework.routing import Rule, Endpoint, Map
from framework.routing.map import Link, Pattern, Callback

from .. import dummy, Dummy


class TestModule(unittest.TestCase):
    def test_blank(self):
        urlmap = Map(())

        for model in (Link(urlmap), Pattern(urlmap), Callback(urlmap)):
            self.assertDictEqual({}, model.__dict__)

    def test_path(self):
        urlmap = Map((
            Rule('/', 'index'),
            Endpoint('index', dummy, 'args'),
            Rule('/<name>', 'slug'),
            Endpoint('slug', (Dummy, 'dummy')),
            Rule('/<int:name>', 'int'),
            Endpoint('int', (Dummy, 'dummy')),
            Rule('/<float:name>', 'float'),
            Endpoint('float', (Dummy, 'dummy')),
        ))

        link = Link(urlmap)

        for args, kwargs in (
                (('/?query=one&two=query', 'index', 'query=one', 'two=query'), {}),
                (('/value?query', 'slug', 'query'), {'name': 'value'}),
                (('/01', 'int'), {'name': '01'}),
                (('/3.14', 'float'), {'name': '3.14'}),
        ):
            self.assertEqual(args[0], link.collect(args[1:], kwargs))

        pattern = Pattern(urlmap)

        for key, model in (
                ('^/$', ('index', ())),
                ('^/([A-Za-z0-9_-]+)$', ('slug', ((0, 'name'),))),
                ('^/(\\d+)$', ('int', ((1, 'name'),))),
                ('^/(\\d+\\.\\d+)$', ('float', ((2, 'name'),))),
        ):
            self.assertTupleEqual(pattern[key], model)

        callback = Callback(urlmap)

        for value, key in (
                (('tests', 'dummy', None, ('args',)), 'index'),
                (('tests', 'Dummy', 'dummy', ()), 'slug'),
                (('tests', 'Dummy', 'dummy', ()), 'int'),
                (('tests', 'Dummy', 'dummy', ()), 'float'),
        ):
            self.assertTupleEqual(value, callback[key])

    def test_token(self):
        urlmap = Map((
            Rule('/<slug>/<or>', 'token',
                 {'slug': '[a-z]+', 'or': (0, '[a-z]+')}),
            Rule('/<slug>/<int>', 'token',
                 {'slug': '[a-z]+', 'int': (1, r'\d{4}')}),
            Rule('/<slug>/<int>/<float>', 'token',
                 {'slug': '[a-z]+', 'int': (1, r'\d{4}'), 'float': (2, r'\d{1}\.\d{2}')}),
            Endpoint('token', Dummy, 'args'),
        ))

        link = Link(urlmap)

        for args, kwargs in (
                (('/slug/or', 'token'), {'slug': 'slug', 'or': 'or'}),
                (('/slug/0001', 'token'), {'slug': 'slug', 'int': '0001'}),
                (('/slug/0001/3.14', 'token'), {'slug': 'slug', 'int': '0001', 'float': '3.14'}),
        ):
            self.assertEqual(args[0], link.collect(args[1:], kwargs))

        pattern = Pattern(urlmap)

        for key, model in (
                ('^/([a-z]+)/([a-z]+)$', ('token', ((0, 'slug'), (0, 'or')))),
                ('^/([a-z]+)/(\\d{4})$', ('token', ((0, 'slug'), (1, 'int')))),
                ('^/([a-z]+)/(\\d{4})/(\\d{1}\\.\\d{2})$', ('token', ((0, 'slug'), (1, 'int'), (2, 'float')))),
        ):
            self.assertTupleEqual(pattern[key], model)

        self.assertTupleEqual(Callback(urlmap)['token'], ('tests', 'Dummy', '__call__', ('args',)))


def map_tests():
    suite = unittest.TestSuite()

    for test in (
            'test_blank',
            'test_path',
            'test_token',
    ):
        suite.addTest(TestModule(test))

    return suite
