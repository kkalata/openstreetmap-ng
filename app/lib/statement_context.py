from contextlib import contextmanager
from contextvars import ContextVar
from typing import TypeVar

from sqlalchemy.orm import joinedload

_joinedload_context = ContextVar('StatementContext_JoinedLoad')

T = TypeVar('T')


@contextmanager
def joinedload_context(*keys):
    """
    Context manager for setting joinedload keys in ContextVar.
    """

    token = _joinedload_context.set(keys)
    try:
        yield
    finally:
        _joinedload_context.reset(token)


def apply_statement_context(stmt: T) -> T:
    """
    Apply statement post-processing context.
    """

    if (keys := _joinedload_context.get(None)) is not None:
        stmt = stmt.options(joinedload(*keys))

    return stmt