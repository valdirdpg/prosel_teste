from collections import namedtuple


class BreadCrumb:
    BreadCrumbItem = namedtuple("BreadCrumbItem", ["name", "url"])

    def __init__(self):
        self.items = []

    def add(self, name, url):
        self.items.append(self.BreadCrumbItem(name, url))

    def add_many(self, items):
        self.items.extend([self.BreadCrumbItem(name, url) for (name, url) in items])

    def __iter__(self):
        return iter(self.items)

    @classmethod
    def create(cls, *items):
        bc = cls()
        bc.add_many(items)
        return bc
