"""In-memory persistence for book records."""

from __future__ import annotations

from typing import Iterable, Iterator

from .custom_map import CustomMap
from .models import Book


class BookRepository:
    """Store books in order and maintain a custom identifier index."""

    __slots__ = ("_books", "_books_by_id")

    def __init__(self, books: Iterable[Book] | None = None) -> None:
        self._books: list[Book] = []
        self._books_by_id: CustomMap[int, Book] = CustomMap()
        if books is not None:
            self.extend(books)

    def add(self, book: Book) -> Book:
        if not isinstance(book, Book):
            raise TypeError("book must be a Book instance")
        book.validate()
        if book.id in self._books_by_id:
            raise ValueError(f"book with id {book.id} already exists")
        self._books.append(book)
        self._books_by_id[book.id] = book
        return book

    def extend(self, books: Iterable[Book]) -> None:
        for book in books:
            self.add(book)

    def get(self, book_id: int) -> Book | None:
        return self._books_by_id.get(book_id)

    def require(self, book_id: int) -> Book:
        book = self.get(book_id)
        if book is None:
            raise KeyError(f"book with id {book_id} was not found")
        return book

    def remove(self, book_id: int) -> Book:
        book = self.require(book_id)
        self._books.remove(book)
        del self._books_by_id[book_id]
        return book

    def replace(self, book: Book) -> Book:
        if not isinstance(book, Book):
            raise TypeError("book must be a Book instance")
        book.validate()
        old_book = self.require(book.id)
        index = self._books.index(old_book)
        self._books[index] = book
        self._books_by_id[book.id] = book
        return book

    def all(self) -> list[Book]:
        return list(self._books)

    def clear(self) -> None:
        self._books.clear()
        self._books_by_id.clear()

    def __contains__(self, value: object) -> bool:
        if isinstance(value, Book):
            return value.id in self._books_by_id
        return value in self._books_by_id

    def __iter__(self) -> Iterator[Book]:
        return iter(self._books)

    def __len__(self) -> int:
        return len(self._books)

    def __bool__(self) -> bool:
        return bool(self._books)
