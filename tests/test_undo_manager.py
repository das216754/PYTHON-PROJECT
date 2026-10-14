import unittest

from facultysync.models import TimeInterval
from facultysync.scheduler import FacultyScheduler
from facultysync.undo_manager import (
    AppointmentNotFoundError,
    NothingToUndoError,
    SlotUnavailableError,
    UndoManager,
)

MEERA = "Dr. Meera"
ARJUN = "Prof. Arjun"


def appt(start, end, faculty=MEERA, day="Monday"):
    return TimeInterval(day, start, end, faculty, kind="appointment")


class UndoManagerTests(unittest.TestCase):

    def setUp(self):
        # Both faculty are available Monday 09:00-12:00 (540-720).
        availability = [
            TimeInterval("Monday", 540, 720, MEERA),
            TimeInterval("Monday", 540, 720, ARJUN),
        ]
        self.scheduler = FacultyScheduler(availability)
        self.undo = UndoManager(self.scheduler)

    # -- helpers that mimic what the admin screens do --------------------
    def slots(self, faculty=MEERA, day="Monday"):
        return list(self.scheduler.appointments.get((day, faculty), []))

    def book(self, a):
        self.scheduler.appointments[(a.day, a.faculty)].append(a)
        self.undo.record_booking(a)

    def cancel(self, a):
        self.scheduler.appointments[(a.day, a.faculty)].remove(a)
        self.undo.record_cancellation(a)

    def reschedule(self, old, new):
        lst = self.scheduler.appointments[(old.day, old.faculty)]
        lst.remove(old)
        self.scheduler.appointments[(new.day, new.faculty)].append(new)
        self.undo.record_reschedule(old, new)

    def add_without_recording(self, a):
        """Someone else takes a slot; the undo stack does not know."""
        self.scheduler.appointments[(a.day, a.faculty)].append(a)

    # -- empty stack -------------------------------------------------------
    def test_undo_on_empty_stack_raises(self):
        self.assertTrue(self.undo.is_empty())
        with self.assertRaises(NothingToUndoError):
            self.undo.undo()

    # -- booking -----------------------------------------------------------
    def test_undo_booking_removes_appointment(self):
        a = appt(540, 570)
        self.book(a)

        undone = self.undo.undo()

        self.assertEqual(self.slots(), [])
        self.assertEqual(undone.kind, "book")
        self.assertTrue(self.undo.is_empty())

    def test_undo_booking_when_appointment_already_gone(self):
        a = appt(540, 570)
        self.book(a)
        self.scheduler.appointments[(a.day, a.faculty)].clear()

        with self.assertRaises(AppointmentNotFoundError):
            self.undo.undo()

        self.assertEqual(self.undo.size(), 1)

    # -- cancellation ------------------------------------------------------
    def test_undo_cancellation_restores_when_slot_free(self):
        a = appt(540, 570)
        self.book(a)
        self.cancel(a)

        # While cancelled the slot is offered to students again.
        offered = self.scheduler.find_slots("Monday", 540, 720)
        self.assertIn(
            {"faculty": MEERA, "day": "Monday", "start": 540, "end": 570},
            offered,
        )

        self.undo.undo()

        self.assertEqual(self.slots(), [a])
        offered = self.scheduler.find_slots("Monday", 540, 720)
        self.assertNotIn(
            {"faculty": MEERA, "day": "Monday", "start": 540, "end": 570},
            offered,
        )

    def test_undo_cancellation_blocked_when_slot_taken(self):
        a = appt(540, 570)
        self.book(a)
        self.cancel(a)
        taken = appt(540, 570)
        self.add_without_recording(taken)

        with self.assertRaises(SlotUnavailableError):
            self.undo.undo()

        self.assertEqual(self.slots(), [taken])
        # The action stays on the stack so it can be retried later.
        self.assertEqual(self.undo.peek().kind, "cancel")
        self.assertEqual(self.undo.size(), 2)

    def test_partial_overlap_blocks_restore(self):
        a = appt(540, 600)
        self.book(a)
        self.cancel(a)
        self.add_without_recording(appt(570, 630))

        with self.assertRaises(SlotUnavailableError):
            self.undo.undo()

    def test_adjacent_appointment_does_not_block_restore(self):
        a = appt(540, 570)
        self.book(a)
        self.cancel(a)
        neighbour = appt(570, 600)
        self.add_without_recording(neighbour)

        self.undo.undo()

        self.assertIn(a, self.slots())
        self.assertIn(neighbour, self.slots())

    def test_other_faculty_same_time_does_not_block_restore(self):
        a = appt(540, 570, MEERA)
        self.book(a)
        self.cancel(a)
        self.add_without_recording(appt(540, 570, ARJUN))

        self.undo.undo()

        self.assertEqual(self.slots(MEERA), [a])

    # -- rescheduling --------------------------------------------------------
    def test_undo_reschedule_restores_old_slot(self):
        old = appt(540, 570)
        new = appt(600, 630)
        self.book(old)
        self.reschedule(old, new)

        undone = self.undo.undo()

        self.assertEqual(self.slots(), [old])
        self.assertEqual(undone.kind, "reschedule")

    def test_undo_reschedule_blocked_keeps_new_slot_in_place(self):
        old = appt(540, 570)
        new = appt(600, 630)
        other = appt(660, 690)
        self.book(old)
        self.book(other)
        self.reschedule(old, new)
        # Slot [other, new] -> someone grabs the old slot meanwhile.
        grabbed = appt(540, 570)
        self.add_without_recording(grabbed)
        before = self.slots()
        size_before = self.undo.size()

        with self.assertRaises(SlotUnavailableError):
            self.undo.undo()

        self.assertEqual(self.slots(), before)
        self.assertEqual(self.undo.size(), size_before)
        self.assertEqual(self.undo.peek().kind, "reschedule")

    # -- stack order ---------------------------------------------------------
    def test_actions_are_undone_in_lifo_order(self):
        a = appt(540, 570)
        b = appt(600, 630)
        self.book(a)
        self.book(b)
        self.cancel(a)

        self.assertEqual(self.undo.undo().kind, "cancel")
        self.assertEqual(sorted(x.start for x in self.slots()), [540, 600])

        self.assertEqual(self.undo.undo().after, b)
        self.assertEqual([x.start for x in self.slots()], [540])

        self.assertEqual(self.undo.undo().after, a)
        self.assertEqual(self.slots(), [])
        self.assertTrue(self.undo.is_empty())

    def test_history_lists_newest_first_with_descriptions(self):
        a = appt(540, 570)
        self.book(a)
        self.cancel(a)

        history = self.undo.history()

        self.assertEqual(history[0].kind, "cancel")
        self.assertEqual(history[1].kind, "book")
        self.assertIn("09:00", history[0].describe())
        self.assertIn(MEERA, history[0].describe())

    # -- availability --------------------------------------------------------
    def test_restore_outside_availability_is_rejected_when_required(self):
        strict = UndoManager(self.scheduler, require_availability=True)
        late = appt(800, 830)  # faculty only available until 12:00
        self.scheduler.appointments[(late.day, late.faculty)].append(late)
        self.scheduler.appointments[(late.day, late.faculty)].remove(late)
        strict.record_cancellation(late)

        with self.assertRaises(SlotUnavailableError):
            strict.undo()

        self.assertEqual(self.slots(), [])

    def test_restore_inside_availability_works_when_required(self):
        strict = UndoManager(self.scheduler, require_availability=True)
        a = appt(540, 570)
        strict.record_cancellation(a)

        strict.undo()

        self.assertEqual(self.slots(), [a])

    # -- misc ------------------------------------------------------------------
    def test_max_history_drops_oldest_action(self):
        small = UndoManager(self.scheduler, max_history=2)
        for start in (540, 570, 600):
            small.record_booking(appt(start, start + 30))

        self.assertEqual(small.size(), 2)
        self.assertEqual(small.peek().after.start, 600)
        self.assertEqual(small.history()[-1].after.start, 570)

    def test_invalid_max_history_rejected(self):
        with self.assertRaises(ValueError):
            UndoManager(self.scheduler, max_history=0)

    def test_recording_none_is_rejected(self):
        with self.assertRaises(ValueError):
            self.undo.record_booking(None)
        with self.assertRaises(ValueError):
            self.undo.record_cancellation(None)
        with self.assertRaises(ValueError):
            self.undo.record_reschedule(appt(540, 570), None)
        self.assertTrue(self.undo.is_empty())


if __name__ == "__main__":
    unittest.main()
