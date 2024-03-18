import re
import time
from datetime import datetime, timedelta, timezone

wd = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
mn = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def format_datetime(dt: datetime):
    if dt.tzinfo is None or dt.tzinfo != timezone.utc:
        raise ValueError('Cookie requires UTC datetime.')

    t = dt.timetuple()

    return '%s, %02d %s %04d %02d:%02d:%02d GMT' % (wd[t[6]], t[2], mn[t[1] - 1], t[0], t[3], t[4], t[5])


class Morsel(object):
    __slots__ = ('value', 'expires', 'max_age', 'path', 'domain', 'secure', 'httponly', 'samesite')

    def __init__(self, name: str, value: str):
        self.value = f"{name}={value}"


class Cookie(object):
    __slots__ = ('name', 'morsel')

    def __init__(self, name: str, value: str):
        self.name, self.morsel = name, Morsel(name, value)

    def __setitem__(self, key: str, value: datetime | timedelta | str | int | float | bool):
        if key in ('domain', 'secure', 'httponly'):
            setattr(self.morsel, key, value)

        else:
            match key:
                case 'expires':
                    self.expires(value)

                case 'max-age':
                    self.max_age(value)

                case 'path':
                    if '' == value:
                        raise ValueError('The path value of a cookie cannot be the empty string.')

                    self.morsel.path = value

                case 'samesite':
                    if value not in ('none', 'lax', 'strict'):
                        raise ValueError(f"The samesite='{value}' cookie value must be 'none', 'lax' or 'strict'.")

                    self.morsel.samesite = value.title()

    def expires(self, value: datetime | str | int | float):
        if isinstance(value, int | float):
            value = datetime.fromtimestamp(value, tz=timezone.utc)

        if isinstance(value, datetime):
            self.morsel.expires = format_datetime(value)

        else:
            if r := re.search(
                    r'^([A-Za-z]{3}), (\d{2}) ([A-Za-z]{3}) (\d{4}) (\d{2}:\d{2}:\d{2}) GMT$', value
            ):
                if r[1] in wd and r[3] in mn:
                    self.morsel.expires = value

            if not hasattr(self.morsel, 'expires'):
                raise ValueError('Datetime string format does not match for cookie.')

    def max_age(self, value: timedelta | int):
        if isinstance(value, timedelta):
            value = int(value.total_seconds())

        if not hasattr(self.morsel, 'expires'):
            self.expires(datetime.fromtimestamp(time.time() + value, timezone.utc))

        self.morsel.max_age = str(value)

    @property
    def value(self):
        value = (morsel := self.morsel).value

        if hasattr(morsel, 'expires'):
            value = f"{value}; expires={morsel.expires}"

        if hasattr(morsel, 'max_age'):
            value = f"{value}; Max-Age={morsel.max_age}"

        if hasattr(morsel, 'path'):
            value = f"{value}; Path={morsel.path}"

        if hasattr(morsel, 'domain'):
            value = f"{value}; Domain={morsel.domain}"

        if hasattr(morsel, 'secure'):
            value = f"{value}; {morsel.secure}"

        if hasattr(morsel, 'httponly'):
            value = f"{value}; {morsel.httponly}"

        if hasattr(morsel, 'samesite'):
            value = f"{value}; SameSite={morsel.samesite}"

        return value


class Header(object):
    __slots__ = ('simple', 'cookie')

    def __init__(self):
        self.simple: dict[str, str] = dict()
        self.cookie: dict[str, str] = dict()

    def headers(self):
        return [(k, v) for k, v in self.simple.items()]

    def cookies(self):
        return [('set-cookie', v) for v in self.cookie.values()]
