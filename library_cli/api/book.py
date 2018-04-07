from typing import List


class Book(object):
    def __init__(self, title: str, authors: List[str], isbn: str, pages: int, quantity=1):
        self.title = title
        self.authors = authors
        self.isbn = isbn
        self.pages = pages
        self.quantity = quantity
        self.borrowers = []
        self.id = None

    def __repr__(self):
        return 'Book(_id={}, title={}, author={}, isbn={}, pages={}, quantity={}, borrowers={})'.format(self.id,
                                                                                                        self.title,
                                                                                                        self.authors,
                                                                                                        self.isbn,
                                                                                                        self.pages,
                                                                                                        self.quantity,
                                                                                                        self.borrowers)
