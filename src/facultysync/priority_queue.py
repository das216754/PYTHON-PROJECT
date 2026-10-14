
"""Priority queue for FacultySync appointment requests."""

import heapq
from dataclasses import dataclass
from datetime import datetime
from itertools import count
from typing import Optional


@dataclass(frozen=True)
class AppointmentRequest:
    request_id: str
    student: str
    faculty: str
    purpose: str
    urgency: int
    deadline: datetime

    def __post_init__(self):
        if not self.request_id.strip():
            raise ValueError("Request ID cannot be empty")
        if not self.student.strip():
            raise ValueError("Student name cannot be empty")
        if not self.faculty.strip():
            raise ValueError("Faculty name cannot be empty")
        if not self.purpose.strip():
            raise ValueError("Purpose cannot be empty")
        if (
            isinstance(self.urgency, bool)
            or not isinstance(self.urgency, int)
            or not 1 <= self.urgency <= 5
        ):
            raise ValueError("Urgency must be an integer from 1 to 5")
        if not isinstance(self.deadline, datetime):
            raise ValueError("Deadline must be a datetime")


class AppointmentPriorityQueue:
    """Higher urgency, earlier deadline, then earlier submission."""

    def __init__(self):
        self._heap = []
        self._sequence = count()
        self._request_ids = set()

    def add_request(self, request: AppointmentRequest) -> None:
        if not isinstance(request, AppointmentRequest):
            raise TypeError("Expected an AppointmentRequest")
        if request.request_id in self._request_ids:
            raise ValueError(f"Duplicate request ID: {request.request_id}")

        heapq.heappush(
            self._heap,
            (
                -request.urgency,
                request.deadline,
                next(self._sequence),
                request,
            ),
        )
        self._request_ids.add(request.request_id)

    def peek_next(self) -> Optional[AppointmentRequest]:
        return self._heap[0][3] if self._heap else None

    def pop_next(self) -> Optional[AppointmentRequest]:
        if not self._heap:
            return None

        _, _, _, request = heapq.heappop(self._heap)
        self._request_ids.remove(request.request_id)
        return request

    def is_empty(self) -> bool:
        return not self._heap

    def __len__(self) -> int:
        return len(self._heap)

    def pending_requests(self) -> list[AppointmentRequest]:
        return [entry[3] for entry in sorted(self._heap)]
