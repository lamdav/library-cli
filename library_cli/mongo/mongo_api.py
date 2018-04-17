from typing import Optional, List, Callable

from bson import DBRef, ObjectId
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
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
            return self.__make_book(result)
        return None

    @staticmethod
    def __make_book(result: dict) -> Book:
        book = Book(title=result.get('title'),
                    authors=result.get('authors'),
                    isbn=result.get('isbn'),
                    pages=result.get('pages'),
                    quantity=result.get('quantity'))

        # Non constructor specifics
        book.id = result.get('_id', None)
        book.borrowers = result.get('borrowers', [])
        return book

    def get_user(self, username: str) -> Optional[User]:
        user_collection = self.__get_collection(USER_COLLECTION)
        search_query = {
            'username': username
        }
        result = user_collection.find_one(search_query)
        if result:
            return self.__make_user(result)
        return None

    @staticmethod
    def __make_user(result: dict) -> User:
        user = User(name=result.get('name'),
                    username=result.get('username'),
                    phone=result.get('phone'))

        # Non constructor specifics
        user.id = result.get('_id', None)
        user.borrowing = result.get('borrowing', [])
        return user

    def add_book(self, book: Book) -> bool:
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

    def edit_book(self, isbn: str, field: str, value: List[str]) -> bool:
        self.info('Editing book isbn={} field={} new_value={}', isbn, field, value)
        if field != 'authors' and len(value) > 1:
            self.error('Field {} only accepts exactly 1 value but got {}', field, value)
            return False
        elif field != 'authors':
            value, *ignore = value

        if field == 'quantity':
            try:
                value = int(value)
            except ValueError:
                self.error('Field {} requires value to be an integer but got {}', field, value)
                return False
            if value < 0:
                self.error('Field {} requires value to be a positive integer by got {}', field, value)

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

    def find_book(self, field: str, value: List[str]) -> List[Book]:
        self.info('Searching for Book with field={} value={}', field, value)
        book_collection = self.__get_collection(BOOK_COLLECTION)

        if field == 'authors':
            search_query = {
                field: {'$all': value}
            }
        elif len(value) == 1:
            value, *ignore = value
            search_query = {
                field: value
            }
        else:
            self.error('Field {} only accepts exactly 1 value but got {}', field, value)
            return []

        cursor = book_collection.find(search_query)
        books = []
        for book in cursor:
            books.append(self.__make_book(book))
        return books

    def find_user(self, field: str, value: str) -> List[User]:
        self.info('Searching for User with field={} value={}', field, value)
        user_collection = self.__get_collection(USER_COLLECTION)

        search_query = {
            field: value
        }
        cursor = user_collection.find(search_query)
        users = []
        for user in cursor:
            users.append(self.__make_user(user))
        return users

    def sort_book_by(self, field: str) -> List[Book]:
        self.info('Sorting Books by {}', field)
        book_collection = self.__get_collection(BOOK_COLLECTION)

        return self.__get_sorted_entity(book_collection, field, self.__make_book)

    def sort_user_by(self, field: str) -> List[User]:
        self.info('Sorting Users by {}', field)
        user_collection = self.__get_collection(USER_COLLECTION)

        return self.__get_sorted_entity(user_collection, field, self.__make_user)

    @staticmethod
    def __get_sorted_entity(collection: Collection, field: str, maker: Callable) -> List:
        cursor = collection.find().sort(field)
        entities = []
        for entity in cursor:
            entities.append(maker(entity))
        return entities

    def check_out_book_for_user(self, isbn: str, username: str) -> bool:
        self.info('Checking out Book isbn={} for User username={}', isbn, username)

        self.info('Retrieving User username={}', username)
        user = self.get_user(username)
        if not user:
            self.error('User username={} does not exist', username)
            return False

        self.info('Retrieving Book isbn={}', isbn)
        book = self.get_book(isbn)
        if not book:
            self.error('Book with isbn={} does not exist', isbn)
            return False

        self.info('Checking Book stock')
        if book.quantity == 0:
            self.error('Book with isbn={} is out of stock', isbn)
            return False

        self.info('Creating references')
        user_ref = DBRef(USER_COLLECTION, user.id, DATABASE)
        book_ref = DBRef(BOOK_COLLECTION, book.id, DATABASE)

        self.info('Updating User username={}', username)
        user_collection = self.__get_collection(USER_COLLECTION)
        user_search_query = {
            '_id': user.id
        }
        user_update_query = {
            '$push': {'borrowing': book_ref}
        }
        user_update_result = user_collection.update_one(user_search_query, user_update_query)

        self.__log_update_result(user_update_result)
        if not user_update_result.acknowledged:
            self.error('User update was not acknowledged')
            return False
        elif not user_update_result.modified_count:
            self.error('User update failed to push book reference {}', book_ref)
            return False

        self.info('Updating Book isbn={}', isbn)
        book_collection = self.__get_collection(BOOK_COLLECTION)
        book_search_query = {
            '_id': book.id
        }
        book_update_query = {
            '$push': {'borrowers': user_ref},
            '$inc': {'quantity': -1}
        }
        book_update_result = book_collection.update_one(book_search_query, book_update_query)

        self.__log_update_result(book_update_result)
        if not book_update_result.acknowledged:
            self.error('Book update was not acknowledge')
            return False
        elif not book_update_result.modified_count:
            self.error('Book update failed to push user reference {}', user_ref)
            return False
        self.success('Checked out Book isbn={} for User username={}', isbn, username)
        return True

    def return_book_for_user(self, isbn: str, username: str) -> bool:
        def get_updated_reference_list(references: List[DBRef], searching: ObjectId):
            updated_references = []
            found = False
            for reference in references:
                if not found and reference.id == searching:
                    found = True
                else:
                    updated_references.append(reference)
            return updated_references, found

        self.info('Returning Book isbn={} for User username={}', isbn, username)

        self.info('Retrieving User username={}', username)
        user = self.get_user(username)
        if not user:
            self.error('User username={} does not exist', username)
            return False

        self.info('Retrieving Book isbn={}', isbn)
        book = self.get_book(isbn)
        if not book:
            self.error('Book with isbn={} does not exist', isbn)
            return False

        self.info('Checking if User username={} has checked out Book isbn={}', username, isbn)
        updated_borrowing, found = get_updated_reference_list(user.borrowing, book.id)
        if not found:
            self.error('User username={} has not checked out Book isbn={}', username, isbn)
            return False

        self.info('Checking if Book isbn={} list User username={} as borrower', isbn, username)
        updated_borrowers, found = get_updated_reference_list(book.borrowers, user.id)
        if not found:
            self.error('Book isbn={} does not have User username={} listed as borrower', username, isbn)
            return False

        user_collection = self.__get_collection(USER_COLLECTION)
        user_search_query = {
            '_id': user.id
        }
        user_update_query = {
            '$set': {'borrowing': updated_borrowing}
        }
        user_update_result = user_collection.update_one(user_search_query, user_update_query)
        self.__log_update_result(user_update_result)

        if not user_update_result.acknowledged:
            self.error('User update was not acknowledged')
            return False
        elif not user_update_result.modified_count:
            self.error('User update failed to update borrowings')
            return False

        book_collection = self.__get_collection(BOOK_COLLECTION)
        book_search_query = {
            '_id': book.id
        }
        book_update_query = {
            '$set': {
                'borrowers': updated_borrowers
            },
            '$inc': {
                'quantity': 1
            }
        }
        book_update_result = book_collection.update_one(book_search_query, book_update_query)

        if not book_update_result.acknowledged:
            self.error('Book update was not acknowledged')
            return False
        elif not book_update_result.modified_count:
            self.error('Book update failed to update borrowers')
            return False

        self.success('Book isbn={} was returned for User user={}', isbn, username)
        return True

    def get_book_stats(self, isbn: str) -> List[User]:
        self.info('Getting who checked out Book isbn={}', isbn)
        book = self.get_book(isbn)
        if not book:
            self.error('Book isbn={} does not exist', isbn)
            return []
        return self.__get_dereferenced_list(book.borrowers, self.__make_user)

    def get_user_stats(self, username: str) -> List[Book]:
        self.info('Getting Books the User username={} has checked out', username)
        user = self.get_user(username)
        if not user:
            self.error('User username={} does not exist', username)
            return []
        return self.__get_dereferenced_list(user.borrowing, self.__make_book)

    def delete_book_field(self, isbn: str, field: str) -> bool:
        self.info('Deleting field {} from Book isbn={}', field, isbn)

        book = self.get_book(isbn)
        if not book:
            self.error('Book isbn={} does not exist', isbn)
            return False
        book_collection = self.__get_collection(BOOK_COLLECTION)

        if not getattr(book, field):
            self.error('Book isbn={} has no field {} to delete', isbn, field)
            return False

        search_query = {
            '_id': book.id
        }
        update_query = {
            '$unset': {
                field: ''  # the value does not matter.
            }
        }
        result = book_collection.update_one(search_query, update_query)
        self.__log_update_result(result)

        if not result.acknowledged:
            self.error('Book field delete was not acknowledged')
            return False
        elif not result.modified_count:
            self.error('Book field delete was unsuccessful')
            return False

        self.success('Book isbn={} no longer has field={}', isbn, field)
        return True

    def delete_user_field(self, username: str, field: str) -> bool:
        self.info('Deleting field {} from User username={}', field, username)

        user = self.get_user(username)
        if not user:
            self.error('User username={} does not exist', username)
            return False

        if not getattr(user, field):
            self.error('User username={} does not exist', username)
            return False

        user_collection = self.__get_collection(USER_COLLECTION)

        search_query = {
            '_id': user.id
        }
        update_query = {
            '$unset': {
                field: ''
            }
        }
        result = user_collection.update_one(search_query, update_query)
        self.__log_update_result(result)

        if not result.acknowledged:
            self.error('User field delete was not acknowledged')
            return False
        elif not result.modified_count:
            self.error('User field delete was unsuccessful')
            return False

        self.success('User username={} no longer has field={}', username, field)
        return True

    def __get_dereferenced_list(self, references: List[DBRef], maker: Callable) -> List:
        db = self.__get_db()
        entities = []
        for reference in references:
            entity = db.dereference(reference)
            entities.append(maker(entity))
        return entities

    def __get_collection(self, collection: str) -> Collection:
        db = self.__get_db()
        return db.get_collection(collection)

    def __get_db(self) -> Database:
        self.client: MongoClient
        return self.client.get_database(DATABASE)

    def __ack_failed(self) -> bool:
        self.error('Mongo failed to acknowledge request')
        return False

    def __log_update_result(self, result: UpdateResult) -> None:
        self.info('acknowledged: {} matched_count: {} modified_count: {} upserted_id: {}', result.acknowledged,
                  result.matched_count, result.modified_count, result.upserted_id)

    def __log_delete_result(self, result: DeleteResult) -> None:
        self.info('acknowledged {} deleted_count: {}', result.acknowledged, result.deleted_count)
