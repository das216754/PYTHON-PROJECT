import pytest

from facultysync.indexes import FacultyIndexes, IndexErrorDuplicate, IndexNotFoundError


@pytest.fixture
def records():
    faculty = [
        {"faculty_id": "F01", "name": "Dr Rao"},
        {"faculty_id": "F02", "name": "Dr Iyer"},
    ]
    students = [
        {"student_id": "S01", "name": "Anu"},
        {"student_id": "S02", "name": "Dev"},
    ]
    bookings = [
        {"booking_id": "B01", "faculty_id": "F01", "time": "10:00"},
        {"booking_id": "B02", "faculty_id": "F01", "time": "11:00"},
        {"booking_id": "B03", "faculty_id": "F02", "time": "12:00"},
    ]
    return faculty, students, bookings


@pytest.fixture
def indexes(records):
    faculty, students, bookings = records
    return FacultyIndexes(faculty, students, bookings)


def test_lookup_faculty_by_id(indexes):
    assert indexes.get_faculty("F01")["name"] == "Dr Rao"


def test_lookup_student_by_id(indexes):
    assert indexes.get_student("S02")["name"] == "Dev"


def test_lookup_booking_by_id(indexes):
    assert indexes.get_booking("B02")["time"] == "11:00"


def test_get_bookings_for_faculty(indexes):
    bookings = indexes.get_bookings_for_faculty("F01")
    assert {b["booking_id"] for b in bookings} == {"B01", "B02"}


def test_unknown_faculty_returns_clear_error(indexes):
    with pytest.raises(IndexNotFoundError):
        indexes.get_faculty("missing")


def test_unknown_booking_returns_clear_error(indexes):
    with pytest.raises(IndexNotFoundError):
        indexes.get_booking("missing")


def test_duplicate_faculty_is_rejected(indexes):
    with pytest.raises(IndexErrorDuplicate):
        indexes.add_faculty({"faculty_id": "F01", "name": "Duplicate"})


def test_duplicate_student_is_rejected(indexes):
    with pytest.raises(IndexErrorDuplicate):
        indexes.add_student({"student_id": "S01", "name": "Duplicate"})


def test_duplicate_booking_is_rejected(indexes):
    with pytest.raises(IndexErrorDuplicate):
        indexes.add_booking(
            {"booking_id": "B01", "faculty_id": "F02", "time": "15:00"}
        )


def test_cancellation_removes_booking_from_all_indexes(indexes):
    removed = indexes.remove_booking("B01")
    assert removed["booking_id"] == "B01"
    assert "B01" not in indexes.booking_by_id
    assert {b["booking_id"] for b in indexes.get_bookings_for_faculty("F01")} == {
        "B02"
    }
    assert indexes.validate()


def test_removing_last_booking_removes_empty_faculty_bucket(indexes):
    indexes.remove_booking("B03")
    assert "F02" not in indexes.bookings_by_faculty_id
    assert indexes.validate()


def test_removing_unknown_booking_raises(indexes):
    with pytest.raises(IndexNotFoundError):
        indexes.remove_booking("missing")


def test_rebuild_bookings_replaces_indexes(records):
    faculty, students, bookings = records
    index = FacultyIndexes(faculty, students, bookings)
    replacement = [
        {"booking_id": "B99", "faculty_id": "F02", "time": "16:00"}
    ]

    index.rebuild_bookings(replacement)

    assert set(index.booking_by_id) == {"B99"}
    assert [b["booking_id"] for b in index.get_bookings_for_faculty("F02")] == [
        "B99"
    ]
    assert index.validate()


def test_rebuild_with_duplicate_does_not_replace_existing_indexes(indexes):
    original_ids = set(indexes.booking_by_id)
    bad_bookings = [
        {"booking_id": "X", "faculty_id": "F01"},
        {"booking_id": "X", "faculty_id": "F02"},
    ]

    with pytest.raises(IndexErrorDuplicate):
        indexes.rebuild_bookings(bad_bookings)

    assert set(indexes.booking_by_id) == original_ids
    assert indexes.validate()


def test_object_records_are_supported():
    class Faculty:
        def __init__(self, faculty_id, name):
            self.faculty_id = faculty_id
            self.name = name

    class Booking:
        def __init__(self, booking_id, faculty_id):
            self.booking_id = booking_id
            self.faculty_id = faculty_id

    faculty = Faculty("F01", "Dr Rao")
    booking = Booking("B01", "F01")
    indexes = FacultyIndexes(faculty=[faculty], bookings=[booking])

    assert indexes.get_faculty("F01") is faculty
    assert indexes.get_booking("B01") is booking
    assert indexes.get_bookings_for_faculty("F01") == [booking]
    assert indexes.validate()
