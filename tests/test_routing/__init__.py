import unittest
from typing import Any

from framework.routing import Rule, Endpoint, Map

from .test_map import map_tests
from .. import dummy, Dummy


class TestModule(unittest.TestCase):
    def test_blank(self):
        urlmap = Map(())

        for attr in urlmap.__slots__:
            self.assertDictEqual({}, getattr(urlmap, attr))

    def test_path(self):
        def callback(link: str, name: str, method: str | None):
            data: tuple[str, str, str | None, tuple[Any, ...]] = urlmap.callback[link]

            self.assertTupleEqual(data[:3], ('tests', name, method))

            return data[3]

        urlmap = Map((
            Rule('/<name>', 'slug'),
            Endpoint('slug', dummy, 'start', 1, True, None, dummy, tuple()),
            Rule('/<int:name>', 'int'),
            Endpoint('int', Dummy),
            Rule('/<float:name>', 'float'),
            Endpoint('float', (Dummy,), 'end')
        ))

        for key, model in (
                ('slug', (('^/([A-Za-z0-9_-]+)$', '/<name>', ('name',)),)),
                ('int', (('^/(\\d+)$', '/<name>', ('name',)),)),
                ('float', (('^/(\\d+\\.\\d+)$', '/<name>', ('name',)),)),
        ):
            self.assertTupleEqual(urlmap.link[key], model)

        for key, model in (
                ('^/([A-Za-z0-9_-]+)$', ('slug', ((0, 'name'),))),
                ('^/(\\d+)$', ('int', ((1, 'name'),))),
                ('^/(\\d+\\.\\d+)$', ('float', ((2, 'name'),))),
        ):
            self.assertTupleEqual(urlmap.pattern[key], model)

        for i in range(0, len(args := callback('slug', 'dummy', None))):
            match i:
                case 0:
                    self.assertEqual(args[i], 'start')

                case 1:
                    self.assertEqual(args[i], 1)

                case 2:
                    self.assertTrue(args[i])

                case 3:
                    self.assertIsNone(args[i])

                case 4:
                    self.assertIsNone(args[i]())

                case 5:
                    self.assertIsInstance(args[i], tuple)

        self.assertTupleEqual(callback('int', 'Dummy', '__call__'), ())
        self.assertEqual(callback('float', 'Dummy', '__call__')[0], 'end')

    def test_token(self):
        urlmap = Map((
            Rule('/<slug>/<or>', 'token',
                 {'slug': r'\d{4}', 'or': (0, r'\d{4}')}),
            Rule('/<slug>/<int>', 'token',
                 {'slug': r'\d{4}', 'int': (1, r'\d{2}')}),
            Rule('/<slug>/<int>/<float>', 'token',
                 {'slug': r'\d{4}', 'int': (1, r'\d{2}'), 'float': (2, r'\d{1}\.\d{2}')}),
            Endpoint('token', (Dummy, 'dummy'))
        ))

        self.assertTupleEqual(urlmap.link['token'], (
            ('^/(\\d{4})/(\\d{4})$', '/<slug>/<or>', ('slug', 'or')),
            ('^/(\\d{4})/(\\d{2})$', '/<slug>/<int>', ('slug', 'int')),
            ('^/(\\d{4})/(\\d{2})/(\\d{1}\\.\\d{2})$', '/<slug>/<int>/<float>', ('slug', 'int', 'float')),
        ))

        for key, model in (
                ('^/(\\d{4})/(\\d{4})$', ('token', ((0, 'slug'), (0, 'or')))),
                ('^/(\\d{4})/(\\d{2})$', ('token', ((0, 'slug'), (1, 'int')))),
                ('^/(\\d{4})/(\\d{2})/(\\d{1}\\.\\d{2})$', ('token', ((0, 'slug'), (1, 'int'), (2, 'float')))),
        ):
            self.assertTupleEqual(urlmap.pattern[key], model)

        self.assertTupleEqual(urlmap.callback['token'], ('tests', 'Dummy', 'dummy', ()))

    def test_raise(self):
        with self.assertRaises(ValueError) as context:
            Map((Rule('', 'link'),))

        self.assertEqual(
            'URL Map. Rule. Path must not be an empty string.',
            context.exception.args[0],
        )

        with self.assertRaises(ValueError) as context:
            Map((Rule('slash', 'link'),))

        self.assertEqual(
            "URL Map. Rule. Path must start slash: 'slash'.",
            context.exception.args[0],
        )

        with self.assertRaises(ValueError) as context:
            Map((Rule('/<error:name>', 'link'),))

        self.assertEqual(
            "URL Map. Rule. Path token has an invalid flag: 'error:name'.",
            context.exception.args[0],
        )

        with self.assertRaises(ValueError) as context:
            Map((Rule('/<pk>', 'link', {'pk': (3, '\\d{2}')}),))

        self.assertEqual(
            r"URL Map. Rule. The added token has an invalid type flag: (3, '\d{2}').",
            context.exception.args[0],
        )

        with self.assertRaises(ValueError) as context:
            Map((Rule('/<int:pk>', 'link', {'pk': (3, '\\d{2}')}),))

        self.assertEqual(
            r"URL Map. Rule. Tokens added to rules have unused values: {'pk': (3, '\\d{2}')}.",
            context.exception.args[0],
        )

        with self.assertRaises(ValueError) as context:
            Map((Rule('/', 'link'), Rule('/', 'link')))

        self.assertEqual(
            "URL Map. Rule. Path already exists in pattern list: '/'.",
            context.exception.args[0],
        )

        with self.assertRaises(ValueError) as context:
            Map((Endpoint('link', dummy), Endpoint('link', dummy)))

        self.assertEqual(
            "URL Map. Endpoint. Link already exists in endpoint list: 'link'.",
            context.exception.args[0],
        )


def routing_tests():
    suite = unittest.TestSuite()

    for test in (
            'test_blank',
            'test_path',
            'test_token',
            'test_raise',
    ):
        suite.addTest(TestModule(test))

    suite.addTests(map_tests())

    return suite
