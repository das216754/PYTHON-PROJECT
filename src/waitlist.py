from datetime import datetime
from collections import deque

class WaitlistEntry:
    def __init__(self, student_id: str, priority: int, timestamp: datetime = None):
        self.student_id = student_id
        self.priority = priority  # Lower number or higher number depending on convention (e.g., 1 = highest priority)
        self.timestamp = timestamp or datetime.now()
        self.status = "active"  # "active", "withdrawn", "expired", "fulfilled"

class AppointmentWaitlist:
    def __init__(self):
        # We can maintain separate deques for each priority level to easily enforce FIFO within priorities
        self.waitlist_queues = {} # key: priority, value: deque of WaitlistEntry

    def add_student(self, student_id: str, priority: int) -> WaitlistEntry:
        """Add a student to the waitlist, preserving FIFO order within their priority category."""
        entry = WaitlistEntry(student_id=student_id, priority=priority)
        if priority not in self.waitlist_queues:
            self.waitlist_queues[priority] = deque()
        self.waitlist_queues[priority].append(entry)
        return entry

    def get_next_eligible_student(self) -> str | None:
        """Finds and removes the next eligible student based on priority rules (highest priority first, then FIFO)."""
        # Sort priorities (assuming lower integer means higher priority, e.g., Priority 1 before Priority 2)
        sorted_priorities = sorted(self.waitlist_queues.keys())
        
        for priority in sorted_priorities:
            queue = self.waitlist_queues[priority]
            while queue:
                entry = queue.popleft()
                if entry.status == "active":
                    entry.status = "fulfilled"
                    return entry.student_id
        return None

    def withdraw_student(self, student_id: str) -> bool:
        """Marks a student's request as withdrawn."""
        found = False
        for priority, queue in self.waitlist_queues.items():
            for entry in queue:
                if entry.student_id == student_id and entry.status == "active":
                    entry.status = "withdrawn"
                    found = True
        return found

    def remove_expired_requests(self, max_age_seconds: int, current_time: datetime = None) -> list[str]:
        """Removes/expires requests older than a certain threshold."""
        current_time = current_time or datetime.now()
        expired_students = []
        
        for priority, queue in self.waitlist_queues.items():
            for entry in queue:
                if entry.status == "active":
                    age = (current_time - entry.timestamp).total_seconds()
                    if age > max_age_seconds:
                        entry.status = "expired"
                        expired_students.append(entry.student_id)
                        
        return expired_students