"""Unit tests for the catalogue domain and services."""

from __future__ import annotations

import unittest

from bookclub.custom_map import CustomMap, MapEntry
from bookclub.models import Book, DomainEntity
from bookclub.repository import BookRepository
from bookclub.seed_data import SeedData
from bookclub.services import BookService


class CustomMapTests(unittest.TestCase):
    def test_insert_update_and_remove_keep_unique_keys(self) -> None:
        values: CustomMap[str, int] = CustomMap([MapEntry("one", 1)])
        values["two"] = 2
        values["one"] = 10

        self.assertEqual(2, len(values))
        self.assertEqual(10, values["one"])
        self.assertEqual(["one", "two"], values.keys())
        self.assertEqual(2, values.remove("two"))
        self.assertNotIn("two", values)

    def test_missing_key_raises_key_error(self) -> None:
        values: CustomMap[int, str] = CustomMap()
        with self.assertRaises(KeyError):
            _ = values[99]


class BookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.book = Book(
            1,
            "Тестовая книга",
            "Автор",
            2020,
            "Проза",
            321,
            4.5,
            "Короткое описание",
        )

    def test_book_is_a_valid_domain_entity(self) -> None:
        self.assertIsInstance(self.book, DomainEntity)
        self.book.validate()
        self.assertEqual(1, self.book.entity_id)

    def test_properties_validate_assigned_values(self) -> None:
        self.book.year = 0
        self.assertEqual(0, self.book.year)
        with self.assertRaises(ValueError):
            self.book.title = "   "
        with self.assertRaises(ValueError):
            self.book.rating = 5.1
        with self.assertRaises(TypeError):
            self.book.pages = True
        with self.assertRaises(TypeError):
            self.book.is_available = 1

    def test_magic_methods_have_domain_meaning(self) -> None:
        equal_book = Book(
            1,
            "Тестовая книга",
            "Автор",
            2020,
            "Проза",
            321,
            4.5,
            "Короткое описание",
        )
        later_book = Book(2, "Яркая книга", "Автор", 2021, "Проза", 200, 4.0)

        self.assertEqual(equal_book, self.book)
        self.assertEqual(hash(equal_book), hash(self.book))
        original_hash = hash(self.book)
        self.book.rating = 3.5
        self.assertEqual(original_hash, hash(self.book))
        self.book.rating = 4.5
        self.assertLess(self.book, later_book)
        self.assertLessEqual(self.book, equal_book)
        self.assertEqual(321, len(self.book))
        self.assertIn("автор", self.book)
        self.assertTrue(self.book)
        self.assertIn("Тестовая книга", str(self.book))
        self.assertIn("Book(", repr(self.book))

    def test_identifier_is_immutable_and_repository_index_stays_consistent(self) -> None:
        repository = BookRepository([self.book])
        original_hash = hash(self.book)

        self.book.id = 1
        self.book.validate()
        with self.assertRaisesRegex(AttributeError, "cannot be changed"):
            self.book.id = 2

        self.assertEqual(original_hash, hash(self.book))
        self.assertIs(self.book, repository.get(1))
        self.assertIsNone(repository.get(2))


class RepositoryAndServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = BookRepository(SeedData.create_books())
        self.service = BookService(self.repository)

    def test_seed_contains_more_than_twelve_independent_books(self) -> None:
        first = SeedData.create_books()
        second = SeedData.create_books()
        self.assertGreaterEqual(len(first), 12)
        self.assertIsNot(first[0], second[0])
        self.assertEqual(first[0], second[0])

    def test_repository_rejects_duplicate_identifier(self) -> None:
        duplicate = Book(1, "Другая", "Автор", 2022, "Проза", 100, 3.0)
        with self.assertRaises(ValueError):
            self.repository.add(duplicate)

    def test_search_filter_sort_and_categories(self) -> None:
        found = self.service.search_books("Пуаро")
        classics = self.service.filter_books(category="классика", min_rating=4.6)
        sorted_books = self.service.sort_books(field="rating", descending=True)

        self.assertEqual([7], [book.id for book in found])
        self.assertEqual([1, 2], [book.id for book in classics])
        self.assertGreaterEqual(sorted_books[0].rating, sorted_books[-1].rating)
        self.assertIn("Фантастика", self.service.categories())

    def test_add_remove_and_toggle(self) -> None:
        new_book = Book(100, "Новая книга", "Новый автор", 2024, "Проза", 240, 4.1)
        self.service.add_book(new_book)
        self.assertIs(new_book, self.service.get_book(100))

        changed = self.service.toggle_availability(100)
        self.assertFalse(changed.is_available)
        removed = self.service.remove_book(100)
        self.assertIs(new_book, removed)
        self.assertIsNone(self.service.get_book(100))

    def test_statistics_use_custom_container(self) -> None:
        statistics = self.service.statistics()
        categories = self.service.category_statistics()
        self.assertIsInstance(statistics, CustomMap)
        self.assertEqual(len(self.repository), statistics["total"])
        self.assertEqual(len(self.service.categories()), statistics["categories"])
        self.assertEqual(3, categories["Классика"])


if __name__ == "__main__":
    unittest.main()
