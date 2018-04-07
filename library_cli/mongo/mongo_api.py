from typing import Optional

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.results import UpdateResult, DeleteResult

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

    def get_book(self, isbn: str) -> Optional[Book]:
        book_collection = self.__get_collection(BOOK_COLLECTION)
        search_query = {
            'isbn': isbn
        }
        result = book_collection.find_one(search_query)
        if result:
            book = Book(title=result.get('title'),
                        authors=result.get('authors'),
                        isbn=result.get('isbn'),
                        pages=result.get('pages'),
                        quantity=result.get('quantity'))

            # Non constructor specifics
            book.id = result.get('_id')
            book.borrowers = result.get('borrowers')
            return book
        return None

    def get_user(self, username: str) -> Optional[User]:
        user_collection = self.__get_collection(USER_COLLECTION)
        search_query = {
            'username': username
        }
        result = user_collection.find_one(search_query)
        if result:
            user = User(name=result.get('name'),
                        username=result.get('username'),
                        phone=result.get('phone'))

            # Non constructor specifics
            user.id = result.get('id')
            user.borrowing = result.get('borrowing')
            return user
        return None

    def add_book(self, book: Book) -> bool:
        self.client: MongoClient

        self.info('Adding {}', book)
        book_collection = self.__get_collection(BOOK_COLLECTION)

        search_query = {'isbn': book.isbn}
        update_query = {
            '$setOnInsert': {
                'isbn': book.isbn,
                'title': book.title,
                'authors': book.authors,
                'pages': book.pages,
                'quantity': book.quantity,
                'borrowers': []
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
        user_collection = self.__get_collection(USER_COLLECTION)

        search_query = {'username': user.username}
        update_query = {
            '$setOnInsert': {
                'name': user.name,
                'username': user.username,
                'phone': user.phone,
                'borrowing': []
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
        book_collection = self.__get_collection(BOOK_COLLECTION)

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
        user_collection = self.__get_collection(USER_COLLECTION)

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

    def remove_book(self, isbn: str) -> bool:
        self.client: MongoClient

        self.info('Removing Book isbn={}', isbn)
        book_collection = self.__get_collection(BOOK_COLLECTION)

        book = self.get_book(isbn)
        if not book:
            self.error('Book with isbn={} does not exist', isbn)
            return False

        search_query = {
            'isbn': isbn,
            'borrowers': {'$size': 0}
        }
        result = book_collection.delete_one(search_query)
        self.__log_delete_result(result)

        if not result.acknowledged:
            return self.__ack_failed()
        elif result.deleted_count:
            self.success('Removed Book with isbn={}', isbn)
            return True
        else:
            self.error('Unable to remove Book with isbn={} as it is checked out by one or more users', isbn)
            return False

    def remove_user(self, username: str) -> bool:
        self.client: MongoClient

        self.info('Removing User username={}', username)
        user_collection = self.__get_collection(USER_COLLECTION)

        user = self.get_user(username)
        if not user:
            self.error('User username={} does not exist', username)
            return False

        search_query = {
            'username': username,
            'borrowing': {'$size': 0}
        }
        result = user_collection.delete_one(search_query)
        self.__log_delete_result(result)

        if not result.acknowledged:
            return self.__ack_failed()
        elif result.deleted_count:
            self.success('Removed User with username={}', username)
            return True
        else:
            self.error('Unable to remove User with username={} as the user has checked out one or more books', username)
            return False

    def __get_collection(self, collection: str) -> Collection:
        db = self.client.get_database(DATABASE)
        return db.get_collection(collection)

    def __ack_failed(self):
        self.error('Mongo failed to acknowledge edit request')
        return False

    def __log_update_result(self, result: UpdateResult):
        self.info('acknowledged: {} matched_count: {} modified_count: {} upserted_id: {}', result.acknowledged,
                  result.matched_count, result.modified_count, result.upserted_id)

    def __log_delete_result(self, result: DeleteResult):
        self.info('acknowledged {} deleted_count: {}', result.acknowledged, result.deleted_count)
