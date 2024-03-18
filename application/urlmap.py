import time
from datetime import datetime, timezone

from framework.http.request import Path
from framework.http.response import (
    url_file, url_for,
    set_header, get_header, has_header, delete_header,
    set_cookie, delete_cookie,
    redirect_page,
    render_template
)


def index():
    start_time = time.time()

    response = render_template('index.html', {
        'file': url_file('style.css'),
        'header': url_for('header', header='one'),
        'cookie': url_for('cookie', cookie='test'),
        'redirect': url_for('redirect', redirect=url_for('header', header='one')),
        'template': url_for('template', filename='block.html'),
        'multipart': url_for('template', filename='multipart.html'),
    })

    print('Index:   ', time.time() - start_time)

    return response


def header(*args, path: Path):
    one, two, three = args
    set_header('header', path.get('header'))
    set_header('delete', 'delete')
    has = has_header('delete')
    delete_header('delete')
    return (
        f"args: {one} {two} {three}\r\n"
        f"path: {path['header']}\r\n"
        f"get:  {get_header('header')}\r\n"
        f"has:  {has}\r\n"
        f"del:  {has_header('delete')}\r\n"
    )


def cookie(path: Path):
    set_cookie(
        'session', 'value',
        datetime.fromtimestamp(time.time() + 60 * 60 * 24, tz=timezone.utc),
        domain='127.0.0.1',
        secure=True,
        httponly=True,
        samesite='lax',
    )
    delete_cookie(path['cookie'], domain='127.0.0.1')
    return f"cookie: {path['cookie']}"


def redirect(path: Path):
    return redirect_page(path['redirect'])


def template(path: Path):
    start_time = time.time()

    filename: str = path['filename']

    response = render_template(filename, {
        'title': filename.split('.')[0].title(),
        'name': 'Guest',
    })

    print('Template:', time.time() - start_time)

    return response
