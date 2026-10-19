"""A small associative container implemented on top of a plain list."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Iterable, Iterator, TypeVar


KeyT = TypeVar("KeyT")
ValueT = TypeVar("ValueT")


@dataclass(slots=True)
class MapEntry(Generic[KeyT, ValueT]):
    """One key-value pair stored by :class:`CustomMap`."""

    key: KeyT
    value: ValueT


class CustomMap(Generic[KeyT, ValueT]):
    """An insertion-ordered key-value collection backed only by entries."""

    __slots__ = ("_entries",)

    def __init__(self, entries: Iterable[MapEntry[KeyT, ValueT]] | None = None) -> None:
        self._entries: list[MapEntry[KeyT, ValueT]] = []
        if entries is not None:
            for entry in entries:
                if not isinstance(entry, MapEntry):
                    raise TypeError("entries must contain MapEntry objects")
                self[entry.key] = entry.value

    def _index_of(self, key: KeyT) -> int:
        for index, entry in enumerate(self._entries):
            if entry.key == key:
                return index
        return -1

    def __getitem__(self, key: KeyT) -> ValueT:
        index = self._index_of(key)
        if index < 0:
            raise KeyError(key)
        return self._entries[index].value

    def __setitem__(self, key: KeyT, value: ValueT) -> None:
        index = self._index_of(key)
        if index < 0:
            self._entries.append(MapEntry(key, value))
        else:
            self._entries[index].value = value

    def __delitem__(self, key: KeyT) -> None:
        index = self._index_of(key)
        if index < 0:
            raise KeyError(key)
        del self._entries[index]

    def __contains__(self, key: object) -> bool:
        for entry in self._entries:
            if entry.key == key:
                return True
        return False

    def __iter__(self) -> Iterator[KeyT]:
        for entry in self._entries:
            yield entry.key

    def __len__(self) -> int:
        return len(self._entries)

    def __bool__(self) -> bool:
        return bool(self._entries)

    def __repr__(self) -> str:
        return f"CustomMap({self._entries!r})"

    def get(self, key: KeyT, default: ValueT | None = None) -> ValueT | None:
        index = self._index_of(key)
        if index < 0:
            return default
        return self._entries[index].value

    def set(self, key: KeyT, value: ValueT) -> None:
        self[key] = value

    def remove(self, key: KeyT) -> ValueT:
        value = self[key]
        del self[key]
        return value

    def keys(self) -> list[KeyT]:
        return [entry.key for entry in self._entries]

    def values(self) -> list[ValueT]:
        return [entry.value for entry in self._entries]

    def items(self) -> list[tuple[KeyT, ValueT]]:
        return [(entry.key, entry.value) for entry in self._entries]

    def clear(self) -> None:
        self._entries.clear()

    def copy(self) -> CustomMap[KeyT, ValueT]:
        duplicate: CustomMap[KeyT, ValueT] = CustomMap()
        for entry in self._entries:
            duplicate[entry.key] = entry.value
        return duplicate
