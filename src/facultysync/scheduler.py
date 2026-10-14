from collections import defaultdict

from .interval_tree import AugmentedIntervalTree


class FacultyScheduler:

    def __init__(self, availability, appointments=None):
        self.trees = defaultdict(AugmentedIntervalTree)
        self.appointments = defaultdict(list)

        # Store faculty availability in interval trees by day
        for interval in availability:
            self.trees[interval.day].insert(interval)

        # Store existing appointments by day and faculty
        for appointment in appointments or []:
            key = (appointment.day, appointment.faculty)
            self.appointments[key].append(appointment)

    def find_slots(
        self, day, student_start, student_end, duration=30
    ):
        if duration <= 0:
            raise ValueError("Duration must be positive")

        # Find faculty intervals overlapping student availability
        intervals = self.trees[day].search_overlaps(
            student_start, student_end
        )

        results = []
        seen = set()

        for interval in intervals:
            start = max(student_start, interval.start)
            end = min(student_end, interval.end)

            cursor = start

            while cursor + duration <= end:
                slot_end = cursor + duration
                key = (day, interval.faculty)

                # Ignore slots that conflict with existing appointments
                conflict = any(
                    appointment.overlaps(cursor, slot_end)
                    for appointment in self.appointments[key]
                )

                unique_key = (
                    interval.faculty, cursor, slot_end
                )

                if not conflict and unique_key not in seen:
                    results.append({
                        "faculty": interval.faculty,
                        "day": day,
                        "start": cursor,
                        "end": slot_end
                    })
                    seen.add(unique_key)

                cursor += duration

        # Return earliest appointment slots first
        return sorted(
            results,
            key=lambda slot: (
                slot["start"], slot["faculty"]
            )
        )