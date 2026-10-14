"""
dictionary-based indexing
fast lookup by faculty ID and booking ID, and group appointments by faculty id

"""

from __future__ import annotations

from collections.abc import Hashable, Iterable, Mapping
from typing import Any


class IndexErrorDuplicate(ValueError):
    """Raised when an ID already exists in an index."""


class IndexNotFoundError(KeyError):
    """Raised when a requested indexed record does not exist."""


class FacultyIndexes:
    """Maintain dictionaries for faculty, students, and appointments.

    Records may be dictionaries or objects with matching attributes.
    Expected identifiers:
      * faculty: faculty_id (or id)
      * student: student_id (or id)
      * booking: booking_id (or id), faculty_id

    The original records are stored as supplied;"""

    def __init__(
        self,
        faculty: Iterable[Any] = (),
        students: Iterable[Any] = (),
        bookings: Iterable[Any] = (),
    ) -> None:
        self.faculty_by_id: dict[Hashable, Any] = {}
        self.student_by_id: dict[Hashable, Any] = {}
        self.booking_by_id: dict[Hashable, Any] = {}
        self.bookings_by_faculty_id: dict[Hashable, dict[Hashable, Any]] = {}

        for record in faculty:
            self.add_faculty(record)
        for record in students:
            self.add_student(record)
        for booking in bookings:
            self.add_booking(booking)

    @staticmethod
    def _get(record: Any, *names: str) -> Any:
        """Read the first available field from a mapping or object."""
        for name in names:
            if isinstance(record, Mapping):
                if name in record:
                    return record[name]
            elif hasattr(record, name):
                return getattr(record, name)
        raise ValueError(
            f"Record {record!r} must provide one of these fields: "
            + ", ".join(names)
        )

    @classmethod
    def _faculty_id(cls, record: Any) -> Hashable:
        value = cls._get(record, "faculty_id", "id")
        try:
            hash(value)
        except TypeError as exc:
            raise ValueError("faculty ID must be hashable") from exc
        return value

    @classmethod
    def _student_id(cls, record: Any) -> Hashable:
        value = cls._get(record, "student_id", "id")
        try:
            hash(value)
        except TypeError as exc:
            raise ValueError("student ID must be hashable") from exc
        return value

    @classmethod
    def _booking_id(cls, record: Any) -> Hashable:
        value = cls._get(record, "booking_id", "id")
        try:
            hash(value)
        except TypeError as exc:
            raise ValueError("booking ID must be hashable") from exc
        return value

    @classmethod
    def _booking_faculty_id(cls, booking: Any) -> Hashable:
        value = cls._get(booking, "faculty_id")
        try:
            hash(value)
        except TypeError as exc:
            raise ValueError("faculty ID must be hashable") from exc
        return value

    def add_faculty(self, faculty: Any) -> None:
        """Add a faculty record; duplicate IDs are rejected."""
        faculty_id = self._faculty_id(faculty)
        if faculty_id in self.faculty_by_id:
            raise IndexErrorDuplicate(f"Faculty ID already exists: {faculty_id!r}")
        self.faculty_by_id[faculty_id] = faculty

    def add_student(self, student: Any) -> None:
        """Add a student record; duplicate IDs are rejected."""
        student_id = self._student_id(student)
        if student_id in self.student_by_id:
            raise IndexErrorDuplicate(f"Student ID already exists: {student_id!r}")
        self.student_by_id[student_id] = student

    def add_booking(self, booking: Any) -> None:
        """Add a booking to the global and faculty-specific indexes.

        If the faculty-specific insertion fails, no partial index update is
        retained.
        """
        booking_id = self._booking_id(booking)
        faculty_id = self._booking_faculty_id(booking)

        if booking_id in self.booking_by_id:
            raise IndexErrorDuplicate(f"Booking ID already exists: {booking_id!r}")

        self.booking_by_id[booking_id] = booking
        self.bookings_by_faculty_id.setdefault(faculty_id, {})[booking_id] = booking

    def remove_booking(self, booking_id: Hashable) -> Any:
        """Remove a booking from every booking index and return it."""
        if booking_id not in self.booking_by_id:
            raise IndexNotFoundError(f"Booking not found: {booking_id!r}")

        booking = self.booking_by_id.pop(booking_id)
        faculty_id = self._booking_faculty_id(booking)
        faculty_bookings = self.bookings_by_faculty_id[faculty_id]
        faculty_bookings.pop(booking_id)

        # Avoid keeping empty buckets for faculty with no appointments.
        if not faculty_bookings:
            del self.bookings_by_faculty_id[faculty_id]

        return booking

    def get_faculty(self, faculty_id: Hashable) -> Any:
        """Return a faculty record by ID."""
        try:
            return self.faculty_by_id[faculty_id]
        except KeyError as exc:
            raise IndexNotFoundError(f"Faculty not found: {faculty_id!r}") from exc

    def get_student(self, student_id: Hashable) -> Any:
        """Return a student record by ID."""
        try:
            return self.student_by_id[student_id]
        except KeyError as exc:
            raise IndexNotFoundError(f"Student not found: {student_id!r}") from exc

    def get_booking(self, booking_id: Hashable) -> Any:
        """Return a booking by ID."""
        try:
            return self.booking_by_id[booking_id]
        except KeyError as exc:
            raise IndexNotFoundError(f"Booking not found: {booking_id!r}") from exc

    def get_bookings_for_faculty(self, faculty_id: Hashable) -> list[Any]:
        """Return all indexed bookings for one faculty member."""
        return list(self.bookings_by_faculty_id.get(faculty_id, {}).values())

    def rebuild_bookings(self, bookings: Iterable[Any]) -> None:
        """Replace both booking indexes from a canonical booking collection.

        The new indexes are built and validated before replacing the old ones,
        so a duplicate or malformed record does not partially overwrite them.
        """
        new_by_id: dict[Hashable, Any] = {}
        new_by_faculty: dict[Hashable, dict[Hashable, Any]] = {}

        for booking in bookings:
            booking_id = self._booking_id(booking)
            faculty_id = self._booking_faculty_id(booking)
            if booking_id in new_by_id:
                raise IndexErrorDuplicate(
                    f"Booking ID already exists: {booking_id!r}"
                )
            new_by_id[booking_id] = booking
            new_by_faculty.setdefault(faculty_id, {})[booking_id] = booking

        self.booking_by_id = new_by_id
        self.bookings_by_faculty_id = new_by_faculty

    def validate(self) -> bool:
        """Check that global and faculty-specific booking indexes agree."""
        total_faculty_bookings = 0
        for faculty_id, bookings in self.bookings_by_faculty_id.items():
            for booking_id, booking in bookings.items():
                if booking_id not in self.booking_by_id:
                    return False
                if self.booking_by_id[booking_id] is not booking:
                    return False
                if self._booking_faculty_id(booking) != faculty_id:
                    return False
                total_faculty_bookings += 1

        return total_faculty_bookings == len(self.booking_by_id)
