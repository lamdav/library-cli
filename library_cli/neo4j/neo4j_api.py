from typing import List

from neo4j.v1 import Driver, CypherError, StatementResult

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
        self.client: Driver
        self.info('adding {}', book)

        with self.client.session() as session:
            self.info('creating book {}', book)
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

            if not self.__run_session(session, statement, params):
                return False

            self.info('linking authors {} to book', book.authors)
            for author in book.authors:
                if not self.__link_author_to_book(session, book.isbn, author):
                    return False

        self.success('added book {}', book)
        return True

    def add_user(self, user: User) -> bool:
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
            if not self.__run_session(session, statement, params):
                return False
        self.success('added new user {}', user)
        return True

    def edit_book(self, isbn: str, field: str, value: List[str]) -> bool:
        self.Client: Driver
        self.info('editing book isbn={} field={} value={}', isbn, field, value)

        if field != 'authors' and len(value) > 1:
            self.error('field {} only accepts exactly 1 value but got {}', field, value)
            return False
        elif field != 'authors':
            value, *ignore = value

        if field == 'quantity' or field == 'pages':
            try:
                value = int(value)
            except ValueError:
                self.error('field {} requires value to be an integer but got {}', field, value)
                return False
            if value < 0:
                self.error('field {} requires value to be a positive integer by got {}', field, value)
                return False

        with self.client.session() as session:
            if field == 'authors':
                self.info('removing existing authors from book isbn={}', isbn)
                statement = '''
                MATCH (book:Book {isbn: {isbn}}) - [relationship:Author_Of] - (author:Author)
                DELETE relationship
                RETURN author
                '''
                params = {
                    'isbn': isbn
                }
                # NOTE: do not call __run_session if using result
                result = session.run(statement, params)

                self.info('cleaning up orphaned authors')
                for record in result.records():
                    author = record['author']
                    statement = '''
                    MATCH (author:Author {name: {name}}) - [relation:Author_Of] - (:Book)
                    RETURN author, COUNT(relation) as count
                    '''
                    params = {
                        'name': author.get('name')
                    }
                    result = session.run(statement, params)
                    for count_record in result.records():
                        if count_record['count'] == 0:
                            self.info('deleting author {} as there are no books with this author', author.get('name'))
                            statement = '''
                            MATCH (author:Author {name: {name}})
                            DELETE author
                            '''
                            params = {
                                'name': author.get('name')
                            }
                            if not self.__run_session(session, statement, params):
                                return False

                self.info('linking new authors {}', value)
                for author in value:
                    if not self.__link_author_to_book(session, isbn, author):
                        return False

            else:
                if field == 'quantity' or field == 'pages':
                    set_statement = 'SET book.{} = {} '.format(field, value)
                else:
                    set_statement = 'SET book.{} = "{}" '.format(field, value)
                statement = 'MATCH (book:Book {isbn: {isbn}}) ' + \
                            set_statement + \
                            'RETURN book'
                params = {
                    'isbn': isbn,
                    'field': field,
                    'value': value
                }
                if not self.__run_session(session, statement, params):
                    return False
        self.success('edited book with field={} and new value={}', field, value)
        return True

    def edit_user(self, username: str, field: str, value: str):
        self.client: Driver

        if field == 'phone':
            try:
                value = int(value)
            except ValueError:
                self.error('field {} requires value to be an integer but got {}', field, value)
                return False

        with self.client.session() as session:
            if field == 'phone':
                set_statement = 'SET user.{} = {} '.format(field, value)
            else:
                set_statement = 'SET user.{} = "{}" '.format(field, value)
            statement = 'MATCH (user:User {username: {username}}) ' + \
                        set_statement + \
                        'RETURN user'
            params = {
                'username': username,
                'field': field,
                'value': value
            }
            if not self.__run_session(session, statement, params):
                return False
        self.success('edited book with field={} and new value={}', field, value)
        return True

    def find_book(self, field: str, value: any):
        self.client: Driver

        with self.client.session() as session:
            if field == 'authors':
                statement = 'MATCH (book:Book) - [relation:Author_Of] - (author:Author)' + \
                            'WHERE author.name IN {}'.format(list(value)) + \
                            'RETURN book, author'
            elif len(value) == 1:
                value, *ignore = value
                statement = 'MATCH (book:Book {' + field + ': "' + value + '"}) - [relation:Author_Of] - (author:Author)' + \
                            'RETURN book, author'


            else:
                self.error('field {} only accepts exactly 1 value but got {}', field, value)
                return []

            try:
                result = session.run(statement)
                books = []
                for record in result.records():
                    books.append((record['book'], record['author']))
                return books
            except CypherError as e:
                self.error(e.message)
                return []

    def find_user(self, field: str, value: str):
        self.client: Driver

        with self.client.session() as session:
            if field == 'phone':
                # do not quote value. phone is an integer.
                match_statement = 'MATCH (user:User {' + field + ': ' + value + '}) '
            else:
                # quote the value
                match_statement = 'MATCH (user:User {' + field + ': "' + value + '"}) '

            statement = match_statement + \
                        'RETURN user'
            try:
                result = session.run(statement)
                users = []
                for record in result.records():
                    users.append(record['user'])
                return users
            except CypherError as e:
                self.error(e.message)
                return []

    def sort_book_by(self, field: str):
        self.client: Driver

        if field == 'authors':
            order_by_statement = 'ORDER BY author.name'
        else:
            order_by_statement = 'ORDER BY book.{}'.format(field)

        with self.client.session() as session:
            statement = 'MATCH (book:Book) - [relation:Author_Of] - (author:Author) ' + \
                        'RETURN book, author ' + \
                        order_by_statement
            try:
                result = session.run(statement)
                books = []
                for record in result.records():
                    books.append((record['book'], record['author']))
                return books
            except CypherError as e:
                self.error('{}', e.message)
                return []

    def __link_author_to_book(self, session, isbn, name):
        statement = '''
        MATCH(book: Book
        {isbn: {isbn}})
        MERGE(author: Author
        {name: {name}})
        CREATE(book) < - [relation: Author_Of] - (author)
        RETURN
        author
        '''
        params = {
            'isbn': isbn,
            'name': name
        }

        return self.__run_session(session, statement, params)

    def __run_session(self, session, statement, params):
        try:
            result = session.run(statement, params)
            self.__log_result(result)
            return True
        except CypherError as e:
            return self.__handle_cyphererror(e)

    def __handle_cyphererror(self, error: CypherError):
        self.error(error.message)
        return False

    def __log_result(self, result: StatementResult):
        for record in result.records():
            for key in record.keys():
                self.info('{}: {}', key, record[key])
