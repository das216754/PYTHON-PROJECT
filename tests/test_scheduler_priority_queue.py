
import unittest
from datetime import datetime, timedelta

from facultysync.priority_queue import AppointmentRequest
from facultysync.scheduler import FacultyScheduler


class TestSchedulerPriorityQueue(unittest.TestCase):

    def setUp(self):
        # Empty availability is sufficient for testing request ordering.
        self.scheduler = FacultyScheduler(availability=[])
        self.deadline = datetime(2026, 10, 20, 17, 0)

    def make_request(self, request_id, urgency, deadline_days=2):
        return AppointmentRequest(
            request_id=request_id,
            student=f"Student {request_id}",
            faculty="Dr. Meera",
            purpose="Project review",
            urgency=urgency,
            deadline=self.deadline + timedelta(days=deadline_days),
        )

    def test_urgent_request_is_processed_first(self):
        normal = self.make_request("R1", urgency=2)
        urgent = self.make_request("R2", urgency=5)

        self.scheduler.submit_request(normal)
        self.scheduler.submit_request(urgent)

        self.assertEqual(
            self.scheduler.peek_priority_request(), urgent
        )
        self.assertEqual(
            self.scheduler.next_priority_request(), urgent
        )
        self.assertEqual(
            self.scheduler.next_priority_request(), normal
        )

    def test_peek_does_not_remove_request(self):
        request = self.make_request("R1", urgency=4)
        self.scheduler.submit_request(request)

        self.assertEqual(self.scheduler.peek_priority_request(), request)
        self.assertEqual(len(self.scheduler.request_queue), 1)


if __name__ == "__main__":
    unittest.main()
