import unittest

from facultysync.models import TimeInterval
from facultysync.interval_tree import AugmentedIntervalTree


class TestAugmentedIntervalTree(unittest.TestCase):

    def setUp(self):
        self.tree = AugmentedIntervalTree()

        self.tree.insert(
            TimeInterval("Monday", 540, 600, "Dr. Meera")
        )
        self.tree.insert(
            TimeInterval("Monday", 630, 690, "Prof. Arjun")
        )
        self.tree.insert(
            TimeInterval("Monday", 720, 780, "Dr. Nisha")
        )

    def test_overlapping_intervals(self):
        results = self.tree.search_overlaps(570, 640)
        names = {item.faculty for item in results}

        self.assertEqual(
            names, {"Dr. Meera", "Prof. Arjun"}
        )

    def test_no_overlap(self):
        results = self.tree.search_overlaps(600, 630)
        self.assertEqual(results, [])

    def test_invalid_range(self):
        results = self.tree.search_overlaps(700, 600)
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()