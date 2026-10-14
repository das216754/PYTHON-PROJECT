class Node:
    def __init__(self, interval):
        self.interval = interval
        self.max_end = interval.end
        self.left = None
        self.right = None


class AugmentedIntervalTree:
    def __init__(self):
        self.root = None

    def insert(self, interval):
        self.root = self._insert(self.root, interval)

    def _insert(self, node, interval):
        if node is None:
            return Node(interval)

        key = (interval.start, interval.end, interval.faculty)
        node_key = (
            node.interval.start,
            node.interval.end,
            node.interval.faculty
        )

        if key < node_key:
            node.left = self._insert(node.left, interval)
        else:
            node.right = self._insert(node.right, interval)

        left_max = node.left.max_end if node.left else -1
        right_max = node.right.max_end if node.right else -1

        node.max_end = max(
            node.interval.end,
            left_max,
            right_max
        )

        return node

    def search_overlaps(self, start, end):
        if start >= end:
            return []

        results = []
        self._search(self.root, start, end, results)
        return results

    def _search(self, node, start, end, results):
        if node is None:
            return

        interval = node.interval

        if interval.start < end and start < interval.end:
            results.append(interval)

        # Search left only if its maximum endpoint can overlap.
        if node.left and node.left.max_end > start:
            self._search(node.left, start, end, results)

        # Search right only if its start range could overlap.
        if node.right and node.interval.start < end:
            self._search(node.right, start, end, results)
