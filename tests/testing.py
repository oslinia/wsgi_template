import unittest

from tests.test_http import http_tests
from tests.test_main import main_tests
from tests.test_routing import routing_tests


def all_test():
    suite = unittest.TestSuite()
    suite.addTests(http_tests())
    suite.addTests(main_tests())
    suite.addTests(routing_tests())

    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(all_test())
