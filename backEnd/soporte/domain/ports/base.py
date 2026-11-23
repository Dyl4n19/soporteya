from collections.abc import Mapping
from typing import Protocol, TypeVar


Entity = TypeVar("Entity")


class RepositoryPort(Protocol[Entity]):
    def list(self, *, search: str = "", filters: Mapping[str, object] | None = None,
             ordering: str | None = None) -> list[Entity]: ...

    def get(self, pk: int) -> Entity: ...

    def save(self, data: Mapping[str, object], pk: int | None = None) -> Entity: ...

    def delete(self, pk: int) -> None: ...
