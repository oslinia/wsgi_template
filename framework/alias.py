from collections.abc import Callable, Generator, Iterable
from types import TracebackType
from typing import Any, Protocol, TypeAlias

HeadersAlias: TypeAlias = list[tuple[str, str]]

_ExcInfo: TypeAlias = tuple[type[BaseException], BaseException, TracebackType]
_OptExcInfo: TypeAlias = _ExcInfo | tuple[None, None, None]


class StartResponse(Protocol):
    def __call__(
            self,
            status: str,
            headers: list[tuple[str, str]],
            exc_info: _OptExcInfo | None = ...,
            /,
    ) -> Callable[[bytes], object]: ...


WSGIEnvironment: TypeAlias = dict[str, Any]
WSGIApplication: TypeAlias = Callable[[WSGIEnvironment, StartResponse], Iterable[bytes]]
WSGIGenerator: TypeAlias = Callable[[StartResponse], Generator[bytes]]
