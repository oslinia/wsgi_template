from framework import Framework
from framework.routing import Rule, Endpoint, Map

from .urlmap import index, header, cookie, redirect, template

app = Framework(__name__, Map((
    Rule('/', 'index'),
    Endpoint('index', index),
    Rule('/header/<header>', 'header'),
    Endpoint('header', header, 'one', 'two', 'three'),
    Rule('/cookie/<cookie>', 'cookie'),
    Endpoint('cookie', cookie),
    Rule('/redirect<redirect>', 'redirect', {'redirect': r'[a-z_/.]+'}),
    Endpoint('redirect', redirect),
    Rule('/template/<filename>', 'template', {'filename': r'[a-z_/.]+'}),
    Endpoint('template', template),
)))
