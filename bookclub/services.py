"""Application services for catalogue operations and session reports."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

from .custom_map import CustomMap
from .models import Book
from .repository import BookRepository


class BookService:
    """Coordinate searching, filtering and changes to the catalogue."""

    __slots__ = ("_repository",)

    def __init__(self, repository: BookRepository) -> None:
        if not isinstance(repository, BookRepository):
            raise TypeError("repository must be a BookRepository instance")
        self._repository = repository

    @property
    def repository(self) -> BookRepository:
        return self._repository

    def all_books(self) -> list[Book]:
        return self._repository.all()

    def get_book(self, book_id: int) -> Book | None:
        return self._repository.get(book_id)

    def add_book(self, book: Book) -> Book:
        return self._repository.add(book)

    def remove_book(self, book_id: int) -> Book:
        return self._repository.remove(book_id)

    def toggle_availability(self, book_id: int) -> Book:
        book = self._repository.require(book_id)
        book.is_available = not book.is_available
        return book

    def set_availability(self, book_id: int, is_available: bool) -> Book:
        book = self._repository.require(book_id)
        book.is_available = is_available
        return book

    def search_books(
        self,
        query: str,
        books: Iterable[Book] | None = None,
    ) -> list[Book]:
        if not isinstance(query, str):
            raise TypeError("query must be a string")
        source = self.all_books() if books is None else list(books)
        return [book for book in source if query in book]

    def filter_books(
        self,
        books: Iterable[Book] | None = None,
        *,
        category: str | None = None,
        author: str | None = None,
        is_available: bool | None = None,
        min_year: int | None = None,
        max_year: int | None = None,
        min_rating: float | None = None,
    ) -> list[Book]:
        source = self.all_books() if books is None else list(books)
        result: list[Book] = []
        normalized_category = category.strip().casefold() if category else None
        normalized_author = author.strip().casefold() if author else None

        for book in source:
            if normalized_category is not None and book.category.casefold() != normalized_category:
                continue
            if normalized_author is not None and normalized_author not in book.author.casefold():
                continue
            if is_available is not None and book.is_available != is_available:
                continue
            if min_year is not None and book.year < min_year:
                continue
            if max_year is not None and book.year > max_year:
                continue
            if min_rating is not None and book.rating < min_rating:
                continue
            result.append(book)
        return result

    @staticmethod
    def _title_sort_key(book: Book) -> tuple[str, str, int]:
        return book.title.casefold(), book.author.casefold(), book.id

    @staticmethod
    def _author_sort_key(book: Book) -> tuple[str, str, int]:
        return book.author.casefold(), book.title.casefold(), book.id

    @staticmethod
    def _year_sort_key(book: Book) -> tuple[int, str, int]:
        return book.year, book.title.casefold(), book.id

    @staticmethod
    def _category_sort_key(book: Book) -> tuple[str, str, int]:
        return book.category.casefold(), book.title.casefold(), book.id

    @staticmethod
    def _pages_sort_key(book: Book) -> tuple[int, str, int]:
        return book.pages, book.title.casefold(), book.id

    @staticmethod
    def _rating_sort_key(book: Book) -> tuple[float, str, int]:
        return book.rating, book.title.casefold(), book.id

    @staticmethod
    def _availability_sort_key(book: Book) -> tuple[bool, str, int]:
        return book.is_available, book.title.casefold(), book.id

    @staticmethod
    def _id_sort_key(book: Book) -> int:
        return book.id

    def sort_books(
        self,
        books: Iterable[Book] | None = None,
        field: str = "title",
        descending: bool = False,
    ) -> list[Book]:
        source = self.all_books() if books is None else list(books)
        normalized_field = field.strip().casefold()

        if normalized_field in ("title", "name"):
            key_method = self._title_sort_key
        elif normalized_field == "author":
            key_method = self._author_sort_key
        elif normalized_field == "year":
            key_method = self._year_sort_key
        elif normalized_field == "category":
            key_method = self._category_sort_key
        elif normalized_field in ("pages", "page_count"):
            key_method = self._pages_sort_key
        elif normalized_field == "rating":
            key_method = self._rating_sort_key
        elif normalized_field in ("availability", "is_available", "available"):
            key_method = self._availability_sort_key
        elif normalized_field in ("id", "book_id"):
            key_method = self._id_sort_key
        elif normalized_field in ("natural", "book"):
            return sorted(source, reverse=descending)
        else:
            raise ValueError(f"unsupported sort field: {field}")
        return sorted(source, key=key_method, reverse=descending)

    def categories(self) -> list[str]:
        result: list[str] = []
        for book in self._repository:
            if not any(existing.casefold() == book.category.casefold() for existing in result):
                result.append(book.category)
        return sorted(result, key=str.casefold)

    def category_statistics(self) -> CustomMap[str, int]:
        result: CustomMap[str, int] = CustomMap()
        for category in self.categories():
            result[category] = 0
        for book in self._repository:
            for category in result:
                if category.casefold() == book.category.casefold():
                    result[category] = result[category] + 1
                    break
        return result

    def statistics(self) -> CustomMap[str, int]:
        total = len(self._repository)
        available = 0
        total_pages = 0
        for book in self._repository:
            if book.is_available:
                available += 1
            total_pages += book.pages

        result: CustomMap[str, int] = CustomMap()
        result["total"] = total
        result["available"] = available
        result["unavailable"] = total - available
        result["categories"] = len(self.categories())
        result["total_pages"] = total_pages
        return result


class SessionReportService:
    """Render and persist login session reports in a stable text format."""

    HEADER = "login | time_in | time_out"
    TIME_FORMAT = "%d.%m.%Y %H:%M:%S"

    @classmethod
    def _validate_session(
        cls,
        login: str,
        time_in: datetime,
        time_out: datetime,
    ) -> str:
        if not isinstance(login, str):
            raise TypeError("login must be a string")
        normalized_login = login.strip()
        if not normalized_login:
            raise ValueError("login cannot be empty")
        if "\n" in normalized_login or "\r" in normalized_login or "|" in normalized_login:
            raise ValueError("login cannot contain line breaks or the separator")
        if not isinstance(time_in, datetime) or not isinstance(time_out, datetime):
            raise TypeError("time_in and time_out must be datetime objects")
        if time_out < time_in:
            raise ValueError("time_out cannot be earlier than time_in")
        return normalized_login

    @classmethod
    def format_session(
        cls,
        login: str,
        time_in: datetime,
        time_out: datetime,
    ) -> str:
        normalized_login = cls._validate_session(login, time_in, time_out)
        return (
            f"{normalized_login} | {time_in.strftime(cls.TIME_FORMAT)} | "
            f"{time_out.strftime(cls.TIME_FORMAT)}"
        )

    @classmethod
    def render_report(
        cls,
        login: str,
        time_in: datetime,
        time_out: datetime,
    ) -> str:
        normalized_login = cls._validate_session(login, time_in, time_out)
        time_in_text = time_in.strftime(cls.TIME_FORMAT)
        time_out_text = time_out.strftime(cls.TIME_FORMAT)
        login_width = max(len("login"), len(normalized_login))
        time_in_width = max(len("time_in"), len(time_in_text))
        time_out_width = max(len("time_out"), len(time_out_text))
        border = (
            "+" + "-" * (login_width + 2)
            + "+" + "-" * (time_in_width + 2)
            + "+" + "-" * (time_out_width + 2) + "+"
        )
        header = (
            f"| {'login':<{login_width}} | {'time_in':<{time_in_width}} | "
            f"{'time_out':<{time_out_width}} |"
        )
        values = (
            f"| {normalized_login:<{login_width}} | {time_in_text:<{time_in_width}} | "
            f"{time_out_text:<{time_out_width}} |"
        )
        return f"{border}\n{header}\n{border}\n{values}\n{border}\n"

    @classmethod
    def write_report(
        cls,
        path: str | Path,
        login: str,
        time_in: datetime,
        time_out: datetime,
        append: bool = False,
    ) -> Path:
        report_path = Path(path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        has_content = append and report_path.exists() and report_path.stat().st_size > 0
        mode = "a" if has_content else "w"
        with report_path.open(mode, encoding="utf-8", newline="\n") as report_file:
            if has_content:
                report_file.write("\n")
            report_file.write(cls.render_report(login, time_in, time_out))
        return report_path
