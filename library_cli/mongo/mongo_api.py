from pymongo import MongoClient

from ..api.book import Book
from ..api.library_api import LibraryAPI
from ..api.user import User
from ..logger import Logger

DATABASE = 'library'
BOOK_COLLECTION = 'book'
USER_COLLECTION = 'user'


class MongoAPI(LibraryAPI):
    def __init__(self, client: MongoClient, logger: Logger):
        super().__init__(client, logger)

    def add_book(self, book: Book):
        self.client: MongoClient

        self.info('Adding {}', book)
        db = self.client.get_database(DATABASE)
        book_collection = db.get_collection(BOOK_COLLECTION)

        search_query = {'isbn': book.isbn}
        update_query = {
            '$setOnInsert': {
                'isbn': book.isbn,
                'title': book.title,
                'authors': book.authors,
                'pages': book.pages,
                'quantity': book.quantity,
                'checked_out': book.checked_out
            }
        }
        result = book_collection.update_one(search_query, update_query, upsert=True)

        if result.upserted_id:
            self.success('Added {}', book)
            return True
        else:
            self.error('Book with ISBN {} already exists', book.isbn)
            return False

    def add_user(self, user: User):
        self.client: MongoClient

        self.info('Adding {}', user)
        db = self.client.get_database(DATABASE)
        user_collection = db.get_collection(USER_COLLECTION)

        search_query = {'username': user.username}
        update_query = {
            '$setOnInsert': {
                'name': user.name,
                'username': user.username,
                'phone': user.phone
            }
        }
        result = user_collection.update_one(search_query, update_query, upsert=True)

        if result.upserted_id:
            self.success('Added {}', user)
            return True
        else:
            self.error('User with username {} already exists', user.username)
            return False
