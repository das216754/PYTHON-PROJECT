"""Stack-based undo system for scheduling actions.

Every booking, cancellation and reschedule is pushed onto a stack (LIFO).
``UndoManager.undo()`` reverses the most recent action, but a restored
slot is first validated against the scheduler's *current* state, so an
admin can only bring back an appointment if the slot is still free.

Real-life use: an administrator accidentally cancels an appointment and
restores it, provided nobody else has taken that slot in the meantime.

The manager works directly on ``FacultyScheduler.appointments``, a dict
keyed by ``(day, faculty)`` whose values are lists of ``TimeInterval``
objects.
"""

from collections import deque
from dataclasses import dataclass

from .models import format_time

BOOK = "book"
CANCEL = "cancel"
RESCHEDULE = "reschedule"


class UndoError(Exception):
    """Base class for every reason an undo can fail."""


class NothingToUndoError(UndoError):
    """The undo stack is empty."""


class SlotUnavailableError(UndoError):
    """The slot that must be restored is no longer available."""


class AppointmentNotFoundError(UndoError):
    """The appointment that must be removed is no longer scheduled."""


@dataclass(frozen=True)
class UndoAction:
    """One reversible scheduling operation.

    kind   -- BOOK, CANCEL or RESCHEDULE
    before -- appointment as it was before the action (None for BOOK)
    after  -- appointment as it is after the action (None for CANCEL)
    """

    kind: str
    before: object = None
    after: object = None

    def describe(self):
        if self.kind == BOOK:
            return f"Booked {_label(self.after)}"
        if self.kind == CANCEL:
            return f"Cancelled {_label(self.before)}"
        return f"Rescheduled {_label(self.before)} -> {_label(self.after)}"


def _label(appointment):
    return (
        f"{appointment.faculty} on {appointment.day} "
        f"{format_time(appointment.start)}-{format_time(appointment.end)}"
    )


class UndoManager:
    """Records scheduling actions and undoes the most recent one.

    scheduler            -- the FacultyScheduler holding current state
    max_history          -- optional cap; the oldest actions are dropped
                            first once the stack is full
    require_availability -- when True, a restored slot must also still
                            lie inside the faculty member's availability
    """

    def __init__(
        self, scheduler, max_history=None, require_availability=False
    ):
        if max_history is not None and max_history <= 0:
            raise ValueError("max_history must be positive")

        self.scheduler = scheduler
        self.require_availability = require_availability
        self._stack = deque(maxlen=max_history)

    # ------------------------------------------------------------------
    # Recording (call these right after the action has been carried out)
    # ------------------------------------------------------------------
    def record_booking(self, appointment):
        self._push(UndoAction(BOOK, None, self._required(appointment)))

    def record_cancellation(self, appointment):
        self._push(UndoAction(CANCEL, self._required(appointment), None))

    def record_reschedule(self, old_appointment, new_appointment):
        self._push(
            UndoAction(
                RESCHEDULE,
                self._required(old_appointment),
                self._required(new_appointment),
            )
        )

    # ------------------------------------------------------------------
    # Inspecting the stack
    # ------------------------------------------------------------------
    def peek(self):
        """Return the most recent action without removing it (or None)."""
        return self._stack[-1] if self._stack else None

    def is_empty(self):
        return not self._stack

    def size(self):
        return len(self._stack)

    def history(self):
        """Actions from newest to oldest."""
        return list(reversed(self._stack))

    # ------------------------------------------------------------------
    # Undo
    # ------------------------------------------------------------------
    def undo(self):
        """Reverse the most recent action and return it.

        Raises NothingToUndoError, SlotUnavailableError or
        AppointmentNotFoundError. When an undo fails the scheduler is
        left exactly as it was and the action stays on top of the stack,
        so the admin can try again later.
        """
        if not self._stack:
            raise NothingToUndoError("Nothing to undo")

        action = self._stack[-1]

        if action.kind == BOOK:
            self._undo_booking(action)
        elif action.kind == CANCEL:
            self._undo_cancellation(action)
        else:
            self._undo_reschedule(action)

        # Only pop once the reversal has fully succeeded.
        return self._stack.pop()

    def _undo_booking(self, action):
        self._remove(action.after)

    def _undo_cancellation(self, action):
        self._validate_slot(action.before)
        self._add(action.before)

    def _undo_reschedule(self, action):
        index = self._remove(action.after)

        try:
            self._validate_slot(action.before)
        except UndoError:
            # Put the new slot back exactly where it was.
            self._add(action.after, index)
            raise

        self._add(action.before)

    # ------------------------------------------------------------------
    # Validation against current availability
    # ------------------------------------------------------------------
    def _validate_slot(self, appointment):
        for existing in self._appointments_for(appointment):
            if existing.overlaps(appointment.start, appointment.end):
                raise SlotUnavailableError(
                    f"Slot no longer available: {_label(appointment)} "
                    f"conflicts with {_label(existing)}"
                )

        if self.require_availability:
            intervals = self.scheduler.trees[appointment.day].search_overlaps(
                appointment.start, appointment.end
            )
            covered = any(
                interval.faculty == appointment.faculty
                and interval.start <= appointment.start
                and appointment.end <= interval.end
                for interval in intervals
            )
            if not covered:
                raise SlotUnavailableError(
                    f"Slot no longer available: {_label(appointment)} "
                    "is outside the faculty member's availability"
                )

    # ------------------------------------------------------------------
    # Scheduler state helpers
    # ------------------------------------------------------------------
    def _appointments_for(self, appointment):
        key = (appointment.day, appointment.faculty)
        return self.scheduler.appointments.get(key, [])

    def _find(self, appointment):
        for index, existing in enumerate(self._appointments_for(appointment)):
            if (
                existing.start == appointment.start
                and existing.end == appointment.end
            ):
                return index
        return None

    def _remove(self, appointment):
        """Remove an appointment and return the index it occupied."""
        index = self._find(appointment)
        if index is None:
            raise AppointmentNotFoundError(
                f"Appointment not found: {_label(appointment)}"
            )
        self._appointments_for(appointment).pop(index)
        return index

    def _add(self, appointment, index=None):
        key = (appointment.day, appointment.faculty)
        slots = self.scheduler.appointments.setdefault(key, [])
        if index is None:
            slots.append(appointment)
        else:
            slots.insert(index, appointment)

    # ------------------------------------------------------------------
    def _push(self, action):
        self._stack.append(action)

    @staticmethod
    def _required(appointment):
        if appointment is None:
            raise ValueError("An appointment is required")
        return appointment
