from contextlib import AbstractContextManager
from typing import Protocol


class UnitOfWorkPort(Protocol):
    def atomic(self) -> AbstractContextManager: ...
