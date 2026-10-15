"""Linked list functions and data structures (pure Python).

The browser visualizer page lives in works/pages/linked_list.py.
"""

MAX_NODES = 10


class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class LinkedList:
    def __init__(self):
        self.head = None
        self.tail = None

    def insert_at_beginning(self, data):
        new_node = Node(data)
        if self.head:
            new_node.next = self.head
            self.head = new_node
        else:
            self.head = new_node
            self.tail = new_node

    def insert_at_end(self, data):
        new_node = Node(data)
        if self.head:
            self.tail.next = new_node
            self.tail = new_node
        else:
            self.tail = new_node
            self.head = new_node

    def insert_after(self, target, data):
        """Insert data right after the first node holding target.

        Returns True when inserted, False when target is not in the list.
        """
        current = self.head
        while current and current.data != target:
            current = current.next
        if not current:
            return False
        new_node = Node(data)
        new_node.next = current.next
        current.next = new_node
        if current is self.tail:
            self.tail = new_node
        return True

    def search(self, data):
        return self.find_index(data) != -1

    def find_index(self, data):
        """Position of the first node holding data, or -1."""
        current = self.head
        index = 0
        while current:
            if current.data == data:
                return index
            current = current.next
            index += 1
        return -1

    def delete(self, data):
        """Remove the first node holding data. Returns the position it had, or -1."""
        previous = None
        current = self.head
        index = 0
        while current:
            if current.data == data:
                if previous:
                    previous.next = current.next
                else:
                    self.head = current.next
                if current is self.tail:
                    self.tail = previous
                return index
            previous = current
            current = current.next
            index += 1
        return -1

    def clear(self):
        """Empty the list and return how many nodes it held."""
        removed = self.size()
        self.head = None
        self.tail = None
        return removed

    def size(self):
        count = 0
        current = self.head
        while current:
            count += 1
            current = current.next
        return count

    def printLinkedList(self):
        """The values in traversal order (the page shows them instead of printing)."""
        values = []
        current = self.head
        while current:
            values.append(current.data)
            current = current.next
        return values
