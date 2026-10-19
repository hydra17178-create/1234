"""Domain objects for the book club application."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date


class DomainEntity(ABC):
    """Common contract implemented by every domain entity."""

    @property
    @abstractmethod
    def entity_id(self) -> int:
        """Return the stable identifier used by repositories."""

    @abstractmethod
    def validate(self) -> None:
        """Raise ``ValueError`` when the entity is not valid."""


class Book(DomainEntity):
    """A validated book record with natural comparison behaviour."""

    __slots__ = (
        "_id",
        "_title",
        "_author",
        "_year",
        "_category",
        "_pages",
        "_rating",
        "_description",
        "_is_available",
    )

    def __init__(
        self,
        id: int,
        title: str,
        author: str,
        year: int,
        category: str,
        pages: int,
        rating: float = 0.0,
        description: str = "",
        is_available: bool = True,
    ) -> None:
        self.id = id
        self.title = title
        self.author = author
        self.year = year
        self.category = category
        self.pages = pages
        self.rating = rating
        self.description = description
        self.is_available = is_available

    @staticmethod
    def _required_text(value: str, field_name: str, maximum: int) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")
        cleaned = value.strip()
        if not cleaned:
            raise ValueError(f"{field_name} cannot be empty")
        if len(cleaned) > maximum:
            raise ValueError(f"{field_name} cannot exceed {maximum} characters")
        return cleaned

    @property
    def entity_id(self) -> int:
        return self.id

    @property
    def id(self) -> int:
        return self._id

    @id.setter
    def id(self, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("id must be an integer")
        if value <= 0:
            raise ValueError("id must be greater than zero")
        if hasattr(self, "_id") and self._id != value:
            raise AttributeError("id cannot be changed after book creation")
        self._id = value

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        self._title = self._required_text(value, "title", 200)

    @property
    def author(self) -> str:
        return self._author

    @author.setter
    def author(self, value: str) -> None:
        self._author = self._required_text(value, "author", 150)

    @property
    def year(self) -> int:
        return self._year

    @year.setter
    def year(self, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("year must be an integer")
        latest_year = date.today().year + 1
        if value < 0 or value > latest_year:
            raise ValueError(f"year must be between 0 and {latest_year}")
        self._year = value

    @property
    def category(self) -> str:
        return self._category

    @category.setter
    def category(self, value: str) -> None:
        self._category = self._required_text(value, "category", 80)

    @property
    def pages(self) -> int:
        return self._pages

    @pages.setter
    def pages(self, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("pages must be an integer")
        if value <= 0 or value > 100_000:
            raise ValueError("pages must be between 1 and 100000")
        self._pages = value

    @property
    def rating(self) -> float:
        return self._rating

    @rating.setter
    def rating(self, value: float) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("rating must be a number")
        numeric_value = float(value)
        if numeric_value < 0.0 or numeric_value > 5.0:
            raise ValueError("rating must be between 0 and 5")
        self._rating = numeric_value

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("description must be a string")
        cleaned = value.strip()
        if len(cleaned) > 2_000:
            raise ValueError("description cannot exceed 2000 characters")
        self._description = cleaned

    @property
    def is_available(self) -> bool:
        return self._is_available

    @is_available.setter
    def is_available(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError("is_available must be a boolean")
        self._is_available = value

    # Aliases keep repository and view code readable in either naming style.
    @property
    def book_id(self) -> int:
        return self.id

    @book_id.setter
    def book_id(self, value: int) -> None:
        self.id = value

    @property
    def page_count(self) -> int:
        return self.pages

    @page_count.setter
    def page_count(self, value: int) -> None:
        self.pages = value

    @property
    def available(self) -> bool:
        return self.is_available

    @available.setter
    def available(self, value: bool) -> None:
        self.is_available = value

    def validate(self) -> None:
        self.id = self.id
        self.title = self.title
        self.author = self.author
        self.year = self.year
        self.category = self.category
        self.pages = self.pages
        self.rating = self.rating
        self.description = self.description
        self.is_available = self.is_available

    def _comparison_key(self) -> tuple[object, ...]:
        return (
            self.title,
            self.author,
            self.year,
            self.category,
            self.pages,
            self.rating,
            self.description,
            self.is_available,
            self.id,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Book):
            return NotImplemented
        return self._comparison_key() == other._comparison_key()

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Book):
            return NotImplemented
        return self._comparison_key() < other._comparison_key()

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Book):
            return NotImplemented
        return self._comparison_key() <= other._comparison_key()

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Book):
            return NotImplemented
        return self._comparison_key() > other._comparison_key()

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Book):
            return NotImplemented
        return self._comparison_key() >= other._comparison_key()

    def __len__(self) -> int:
        return self.pages

    def __hash__(self) -> int:
        return hash(self.id)

    def __contains__(self, text: object) -> bool:
        if not isinstance(text, str):
            return False
        query = text.strip().casefold()
        return any(
            query in candidate.casefold()
            for candidate in (self.title, self.author, self.category, self.description)
        )

    def __bool__(self) -> bool:
        return self.is_available

    def __repr__(self) -> str:
        return (
            "Book("
            f"id={self.id!r}, title={self.title!r}, author={self.author!r}, "
            f"year={self.year!r}, category={self.category!r}, pages={self.pages!r}, "
            f"rating={self.rating!r}, description={self.description!r}, "
            f"is_available={self.is_available!r})"
        )

    def __str__(self) -> str:
        status = "available" if self.is_available else "unavailable"
        return f"{self.title} by {self.author} ({self.year}), {status}"
