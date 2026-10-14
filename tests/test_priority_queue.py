
import unittest
from datetime import datetime, timedelta

from facultysync.priority_queue import (
    AppointmentRequest,
    AppointmentPriorityQueue,
)


class TestAppointmentPriorityQueue(unittest.TestCase):

    def setUp(self):
        self.queue = AppointmentPriorityQueue()
        self.now = datetime(2026, 10, 14, 10, 0)

    def make_request(
        self, request_id, urgency=3, deadline_days=3
    ):
        return AppointmentRequest(
            request_id=request_id,
            student=f"Student {request_id}",
            faculty="Dr. Meera",
            purpose="Project review",
            urgency=urgency,
            deadline=self.now + timedelta(days=deadline_days),
        )

    def test_higher_urgency_first(self):
        normal = self.make_request("R1", urgency=2)
        urgent = self.make_request("R2", urgency=5)

        self.queue.add_request(normal)
        self.queue.add_request(urgent)

        self.assertEqual(self.queue.pop_next(), urgent)
        self.assertEqual(self.queue.pop_next(), normal)

    def test_earlier_deadline_breaks_tie(self):
        later = self.make_request(
            "R1", urgency=4, deadline_days=5
        )
        earlier = self.make_request(
            "R2", urgency=4, deadline_days=1
        )

        self.queue.add_request(later)
        self.queue.add_request(earlier)

        self.assertEqual(self.queue.pop_next(), earlier)
        self.assertEqual(self.queue.pop_next(), later)

    def test_equal_priority_preserves_submission_order(self):
        first = self.make_request(
            "R1", urgency=4, deadline_days=2
        )
        second = self.make_request(
            "R2", urgency=4, deadline_days=2
        )
        third = self.make_request(
            "R3", urgency=4, deadline_days=2
        )

        for request in (first, second, third):
            self.queue.add_request(request)

        self.assertEqual(self.queue.pop_next(), first)
        self.assertEqual(self.queue.pop_next(), second)
        self.assertEqual(self.queue.pop_next(), third)

    def test_peek_does_not_remove_request(self):
        request = self.make_request("R1")
        self.queue.add_request(request)

        self.assertEqual(self.queue.peek_next(), request)
        self.assertEqual(len(self.queue), 1)

    def test_empty_queue(self):
        self.assertTrue(self.queue.is_empty())
        self.assertIsNone(self.queue.peek_next())
        self.assertIsNone(self.queue.pop_next())

    def test_duplicate_request_id_rejected(self):
        self.queue.add_request(self.make_request("R1"))

        with self.assertRaises(ValueError):
            self.queue.add_request(self.make_request("R1"))

    def test_invalid_urgency_rejected(self):
        with self.assertRaises(ValueError):
            self.make_request("R1", urgency=6)

    def test_pending_requests_preserves_queue(self):
        normal = self.make_request("R1", urgency=2)
        urgent = self.make_request("R2", urgency=5)

        self.queue.add_request(normal)
        self.queue.add_request(urgent)

        self.assertEqual(
            self.queue.pending_requests(),
            [urgent, normal],
        )
        self.assertEqual(len(self.queue), 2)


if __name__ == "__main__":
    unittest.main()
