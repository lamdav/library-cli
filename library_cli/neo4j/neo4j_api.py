from typing import List

from neo4j.v1 import Driver, CypherError, Session

from ..api.book import Book
from ..api.library_api import LibraryAPI
from ..api.user import User
from ..logger import Logger


class Neo4jAPI(LibraryAPI):
    def __init__(self, client: Driver, logger: Logger):
        super().__init__(client, logger)
        self.__setup()

    def __setup(self):
        self.client: Driver
        self.log_tag('INIT')

        with self.client.session() as session:
            self.info('setting up isbn uniqueness and existence constraint')
            statement = 'CREATE CONSTRAINT ON (book:Book) ASSERT (book.isbn) IS NODE KEY'
            session.run(statement)

            existence_constraints = ['title', 'pages', 'quantity']
            self.info('setting up existence constraints for book: {}', existence_constraints)
            for constraint in existence_constraints:
                statement = 'CREATE CONSTRAINT ON (book:Book) ASSERT EXISTS(book.{})'.format(constraint)
                session.run(statement)

            self.info('setting up username uniqueness and existence constraint')
            statement = 'CREATE CONSTRAINT ON (user:User) ASSERT (user.username) IS NODE KEY'
            session.run(statement)

            existence_constraints = ['phone', 'name']
            self.info('setting up existence constraints for user: {}', existence_constraints)
            for constraint in existence_constraints:
                statement = 'CREATE CONSTRAINT ON (user:User) ASSERT EXISTS(user.{})'.format(constraint)
                session.run(statement)

            self.info('setting up author name uniqueness and existence constraint')
            statement = 'CREATE CONSTRAINT ON (author:Author) ASSERT (author.name) IS NODE KEY'
            session.run(statement)

    def add_book(self, book: Book) -> bool:
        """
        Add a Book to the library.

        :return: True if successful. False otherwise.
        """
        self.client: Driver
        self.info('adding {}', book)

        with self.client.session() as session:
            statement = '''
            CREATE (book:Book {isbn: {isbn}, title: {title}, pages: {pages}, quantity: {quantity}})
            RETURN book
            '''
            params = {
                'isbn': book.isbn,
                'title': book.title,
                'pages': book.pages,
                'quantity': book.quantity
            }

            try:
                result = session.run(statement, params)
                for record in result.records():
                    self.info('record: {}', record)
            except CypherError as e:
                return self.__handle_cyphererror(e, session)

            statement = '''
            MATCH (book:Book {isbn: {isbn}})
            MERGE (author:Author {name: {name}})
            CREATE (book) <- [relation:Author_Of] - (author)
            RETURN book, author
            '''
            for author in book.authors:
                params = {
                    'isbn': book.isbn,
                    'name': author
                }
                try:
                    result = session.run(statement, params)
                    for record in result.records():
                        self.info('record: {}', record)
                except CypherError as e:
                    return self.__handle_cyphererror(e, session)
        return True

    def add_user(self, user: User) -> bool:
        """
        Add a User to the library.

        :return: True if successful. False otherwise.
        """
        self.client: Driver
        self.info('adding {}', user)

        with self.client.session() as session:
            statement = '''
            CREATE (user:User {username: {username}, name: {name}, phone: {phone}})
            RETURN user
            '''
            params = {
                'username': user.username,
                'name': user.name,
                'phone': user.phone
            }
            try:
                result = session.run(statement, params)
                for record in result.records():
                    self.info('record: {}', record)
            except CypherError as e:
                return self.__handle_cyphererror(e, session)

    def edit_book(self, isbn: str, field: str, value: List[str]) -> bool:
        """
        Edit a Book in the library.

        :return: True if successful. False otherwise.
        """

        raise NotImplementedError

    def __handle_cyphererror(self, error: CypherError, session: Session):
        self.error(error.message)
        session.close()
        return False
