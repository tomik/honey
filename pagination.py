
from flask import url_for


class Pagination(object):
    """Simple pagination class."""

    def __init__(self, per_page, page, count, url_maker, neighbours=5):
        self.per_page = per_page
        self.page = page
        self.count = count
        self.url_maker = url_maker
        self.neighbours = 5

    def url_for(self, page):
        return self.url_maker(page)

    def __iter__(self):
        if self.has_previous():
            yield 1
            batch_lo = max(2, self.page - self.neighbours)
            if batch_lo > 2:
                yield None
            for p in range(batch_lo, self.page):
                yield p

        yield self.page

        if self.has_next():
            batch_hi = min(self.pages, self.page + self.neighbours + 1)
            for p in range(self.page + 1, batch_hi):
                yield p
            if batch_hi < self.pages:
                yield None
            yield self.pages

    def has_previous(self):
        return self.page > 1 

    def has_next(self):
        return self.page < self.pages

    @property
    def previous(self):
        return self.url_for(self.page - 1)

    @property
    def next(self):
        return self.url_for(self.page + 1)

    @property
    def pages(self):
        return max(0, self.count - 1) // self.per_page + 1
