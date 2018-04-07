from pymongo import MongoClient
from pymongo.results import UpdateResult

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

    def add_book(self, book: Book) -> bool:
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
        self.__log_update_result(result)

        if not result.acknowledged:
            return self.__ack_failed()
        elif result.upserted_id:
            self.success('Added {}', book)
            return True
        else:
            self.error('Book with ISBN {} already exists', book.isbn)
            return False

    def add_user(self, user: User) -> bool:
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
        self.__log_update_result(result)

        if not result.acknowledged:
            return self.__ack_failed()
        elif result.upserted_id:
            self.success('Added {}', user)
            return True
        else:
            self.error('User with username {} already exists', user.username)
            return False

    def edit_book(self, isbn: str, field: str, value: any) -> bool:
        self.client: MongoClient

        self.info('Editing book isbn={} field={} new_value={}', isbn, field, value)
        db = self.client.get_database(DATABASE)
        book_collection = db.get_collection(BOOK_COLLECTION)

        search_query = {'isbn': isbn}
        update_query = {
            '$set': {
                field: value
            }
        }
        result = book_collection.update_one(search_query, update_query)
        self.__log_update_result(result)

        if not result.acknowledged:
            return self.__ack_failed()
        if result.modified_count and result.matched_count:
            self.info('Book with isbn={} was found and updated', isbn)
            self.success('Updated Book isbn={} field={} value={}', isbn, field, value)
            return True
        elif result.matched_count:
            self.info('Book with isbn={} was found and not updated', isbn)
            self.success('No update was needed to be done to Book isbn={}', isbn)
            return True
        else:
            self.error('Book with isbn={} does not exists', isbn)
            return False

    def edit_user(self, username: str, field: str, value: str) -> bool:
        self.client: MongoClient

        self.info('Editing User username={} field={} new_value={}', username, field, value)
        db = self.client.get_database(DATABASE)
        user_collection = db.get_collection(USER_COLLECTION)

        search_query = {'username': username}
        update_query = {
            '$set': {
                field: value
            }
        }
        result = user_collection.update_one(search_query, update_query)
        self.__log_update_result(result)

        if not result.acknowledged:
            return self.__ack_failed()
        if result.modified_count and result.matched_count:
            self.info('User with username={} was found and updated', username)
            self.success('Updated User username={} field={} value={}', username, field, value)
            return True
        elif result.matched_count:
            self.info('User with username={} was found and not updated', username)
            self.success('No update was needed to be done to User username={}', username)
            return True
        else:
            self.error('User with username={} does not exists', username)
            return False

    def __log_update_result(self, result: UpdateResult):
        self.info('acknowledge: {} matched_count: {} modified_count: {} upserted_id: {}', result.acknowledged,
                  result.matched_count, result.modified_count, result.upserted_id)

    def __ack_failed(self):
        self.error('Mongo failed to acknowledge edit request')
        return False
