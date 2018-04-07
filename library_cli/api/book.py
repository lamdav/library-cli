from typing import List


class Book(object):
    def __init__(self, title: str, authors: List[str], isbn: str, pages: int, quantity=1):
        self.title = title
        self.authors = authors
        self.isbn = isbn
        self.pages = pages
        self.quantity = quantity
        self.checked_out = 0

    def __repr__(self):
        return 'Book(title={}, author={}, isbn={}, pages={}, quantity={}, checked_out={})'.format(self.title,
                                                                                                  self.authors,
                                                                                                  self.isbn,
                                                                                                  self.pages,
                                                                                                  self.quantity,
                                                                                                  self.checked_out)
