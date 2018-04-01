import pathlib
import sys

sys.path.append(pathlib.Path().cwd().as_posix())
import click
from redis import Redis

from config import Config

config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Print all logs')
@config
def cli(config: Config, verbose: bool):
    config.verbose = verbose
    config.redis = Redis(charset='utf-8', decode_responses=True)
    config.key_type_to_book_set_map = {
        'title': 'title:book_set',
        'author': 'author:book_set',
        'isbn': 'isbn:book_set'
    }
    config.all_books_key = 'books'

    config.key_type_to_user_set_map = {
        'name': 'name:user_set',
        'username': 'username:user_set',
        'phone': 'phone:user_set'
    }


@cli.command()
@click.argument('title')
@click.argument('author')
@click.argument('isbn')
@click.argument('pages', type=int)
@click.argument('quantity', type=int, default=1)
@config
def add_book(config: Config, title: str, author: str, isbn: str, pages: int, quantity: int):
    """
    Add a book to the library.
    """
    redis = config.redis
    key_type_to_book_set_map = config.key_type_to_book_set_map

    def create_entry():
        # Create a basic book entity.
        ID_COUNTER = 'book_id_counter'
        current_book_id = redis.incr(ID_COUNTER)
        book_id = 'book:{}'.format(current_book_id)
        _info('Storing id={} title={} author={} isbn={} pages={}', book_id, title, author, isbn, pages)
        redis.hset(book_id, 'title', title)
        redis.hset(book_id, 'author', author)
        redis.hset(book_id, 'isbn', isbn)
        redis.hset(book_id, 'pages', pages)
        redis.hset(book_id, 'quantity', quantity)
        _success('Created book entry')
        return book_id

    def add_book_entry_to_tracking_set(tracking_set_key, tracking_set_type, tracking, book_id):
        _info('Checking for existence of hset={} key={}', tracking_set_key, tracking)
        if redis.hexists(tracking_set_key, tracking):
            _info('Found hset={} key={}', tracking_set_key, tracking)
            book_set_key = redis.hget(tracking_set_key, tracking)
        else:
            BOOK_SET_ID_COUNTER = '{}:book_set_id_counter'.format(tracking_set_key)
            book_set_id = redis.incr(BOOK_SET_ID_COUNTER)
            book_set_key = '{}:{}:book_set{}'.format(tracking_set_type, tracking, book_set_id)
            _info('Creating hset={} key={} value={}', tracking_set_key, tracking, book_set_key)
            redis.hset(tracking_set_key, tracking, book_set_key)
        redis.sadd(book_set_key, book_id)
        _success('Added set={} key={}', book_set_key, book_id)

    # Add only if the isbn is not already in the library.
    if _in_library(redis, isbn, key_type_to_book_set_map):
        _error('Attempting to add a book that already exist. Use `edit_book` to edit the book\'s fields')
        sys.exit(1)

    # Process:
    # 1. Create book entry.
    # 2. Link each title:book_set, author:book_set, isbn:book_set with a new set or existing set
    # 2a. If existing, then search will pair these up. Ex: same titles.
    # 2b. If not, it is a brand new entry.
    # 2c. Only isbn should remain unique. (verified above)
    # 3. Add book_id to sets.
    # (field:book_set) -> book_set_id -> book_set_id -> book
    book_id = create_entry()
    book_dict = {
        'title': title,
        'author': author,
        'isbn': isbn,
        'pages': pages,
        'quantity': quantity
    }
    for book_set_type, book_set_key in key_type_to_book_set_map.items():
        add_book_entry_to_tracking_set(book_set_key, book_set_type, book_dict.get(book_set_type), book_id)
    redis.sadd('books', book_id)


@cli.command()
@click.argument('name')
@click.argument('username')
@click.argument('phone', type=int)
@config
def add_user(config: Config, name: str, username: str, phone: int):
    """
    Add a user
    """
    redis = config.redis
    key_type_to_user_set_map = config.key_type_to_user_set_map

    def create_user():
        ID_COUNTER = 'user_id_counter'
        user_id = 'user:{}'.format(redis.incr(ID_COUNTER))
        redis.hset(user_id, 'name', name)
        redis.hset(user_id, 'username', username)
        redis.hset(user_id, 'phone', phone)
        return user_id

    def add_user_to_tracking_set(tracking_set_key, tracking_set_type, tracking, user_id):
        _info('Checking for existence of hset={} key={}', tracking_set_key, tracking)
        if redis.hexists(tracking_set_key, tracking):
            _info('Found hset={} key={}', tracking_set_key, tracking)
            user_set_key = redis.hget(tracking_set_key, tracking)
        else:
            USER_SET_ID_COUNTER = '{}:user_set_id_counter'.format(tracking_set_key)
            user_set_id = redis.incr(USER_SET_ID_COUNTER)
            user_set_key = '{}:{}:user_set{}'.format(tracking_set_type, tracking, user_set_id)
            _info('Creating hset={} key={} value={}', tracking_set_key, tracking, user_set_key)
            redis.hset(tracking_set_key, tracking, user_set_key)
        redis.sadd(user_set_key, user_id)
        _success('Added set={} key={}', user_set_key, user_id)

    if _in_library(redis, username, key_type_to_user_set_map):
        sys.exit(1)

    # Process:
    # 1. Create user
    # 2. Link user to name:user_set and username:user_set
    user_id = create_user()
    user = {
        'name': name,
        'username': username,
        'phone': phone
    }
    for field, field_key in key_type_to_user_set_map.items():
        add_user_to_tracking_set(field_key, field, user.get(field), user_id)


@cli.command()
@click.argument('entity', type=click.Choice(['user', 'book']))
@click.argument('identifier')
@config
def remove(config: Config, entity: str, identifier: str):
    """
    Remove a book from the library.
    """
    redis = config.redis

    if entity == 'book':
        key_type_map = config.key_type_to_book_set_map
    else:
        key_type_map = config.key_type_to_user_set_map

    # Remove entity that are in the library.
    if not _in_library(redis, identifier, key_type_map):
        _warn('{} {} does not exist', entity, identifier)
        sys.exit(1)

    # Get book_set (will have cardinaity=1)
    entity_set = _get_by_identifier(redis, identifier, key_type_map)

    for entity_id in entity_set:
        # Clean up the field:book_sets and book_sets.
        for field_type, field_to_set_key in key_type_map.items():
            # Get the value of the book (i.e. title, author, etc.)
            field_value = redis.hget(entity_id, field_type)

            # Remove entry from set of book_id
            field_set_id = redis.hget(field_to_set_key, field_value)
            _info('removing set={} key={}', field_set_id, entity_id)
            redis.srem(field_set_id, entity_id)

            # If it is empty after removal, remove book_set from field:book_sets.
            # This means there are no other fields with say title 'hello'.
            if redis.scard(field_set_id) == 0:
                _info('deleting set={}', field_set_id)
                redis.delete(field_set_id)
                _info('removing hset={} key={}', field_to_set_key, field_value)
                redis.hdel(field_to_set_key, field_value)

        if entity == 'book':
            _info('removing set=books book_id={}', entity_id)
            redis.srem('books', entity_id)
        _info('deleting entity_id={}', entity_id)
        redis.delete(entity_id)


@cli.command()
@click.argument('isbn')
@click.argument('field', type=click.Choice(['title', 'author', 'pages', 'quantity']))
@click.argument('value')
@config
def edit_book(config: Config, isbn: str, field: str, value: str):
    """
    Edit a book from the library.
    """
    _info('Editing book with isbn={} field={} value={}', isbn, field, value)

    redis = config.redis
    key_type_to_book_set = config.key_type_to_book_set_map
    if not _in_library(redis, isbn, key_type_to_book_set):
        _error('Attempting to edit a book that does not exist.')
        sys.exit(1)

    # Cardinality=1 for isbn sets.
    book_set = _get_by_identifier(redis, isbn, key_type_to_book_set)
    for book_id in book_set:
        # Update the book.
        _info('Updating hset={} key={} value={}', book_id, field, value)
        old_value = redis.hget(book_id, field)
        redis.hset(book_id, field, value)

        # Get old data.
        tracking_set_key = key_type_to_book_set.get(field)
        book_set_key = redis.hget(tracking_set_key, old_value)
        if redis.hexists(tracking_set_key, value):
            _info('New book_set_key already exist. Merging with existing key.')
            updated_book_set_key = redis.hget(tracking_set_key, value)
        else:
            _info('New book_set_key does not exist. Creating new key.')
            BOOK_SET_ID_COUNTER = '{}:book_set_id_counter'.format(tracking_set_key)
            book_set_id = redis.incr(BOOK_SET_ID_COUNTER)
            updated_book_set_key = '{}:{}:book_set{}'.format(field, value, book_set_id)
            _info('Creating hset={} key={} value={}', tracking_set_key, value, updated_book_set_key)
            redis.hset(tracking_set_key, value, updated_book_set_key)

        if book_set_key is None:
            _info('No tracking set needs to be updated for field={}', field)
        else:
            _info('Adding set={} book_id={}', updated_book_set_key, book_id)
            redis.sadd(updated_book_set_key, book_id)
            _info('Updating hset={} key={} value={}', tracking_set_key, value, updated_book_set_key)
            redis.hset(tracking_set_key, value, updated_book_set_key)

            _info('Removing set={} book_id={}', book_set_key, book_id)
            redis.srem(book_set_key, book_id)
            if redis.scard(book_set_key) == 0:
                _info('Cleaning up book set={}', book_set_key)
                redis.delete(book_set_key)
                redis.hdel(tracking_set_key, old_value)

    _success('Edited book with isbn={} field={} value={}', isbn, field, value)


@cli.command()
@click.argument('username')
@click.argument('field', type=click.Choice(['name', 'phone']))
@click.argument('value')
@config
def edit_user(config: Config, username: str, field: str, value: str):
    """
    Edit a user from the library.
    """
    _info('Editing user with username={} field={} value={}', username, field, value)

    redis = config.redis
    key_type_to_user_set_map = config.key_type_to_user_set_map
    if not _in_library(redis, username, key_type_to_user_set_map):
        sys.exit(1)

    # Cardinality=1 for isbn sets.
    user_set = _get_by_identifier(redis, username, key_type_to_user_set_map)
    for user_id in user_set:
        # Update the book.
        _info('Updating hset={} key={} value={}', user_id, field, value)
        old_value = redis.hget(user_id, field)
        redis.hset(user_id, field, value)

        # Get old data.
        tracking_set_key = key_type_to_user_set_map.get(field)
        user_set_key = redis.hget(tracking_set_key, old_value)
        if redis.hexists(tracking_set_key, value):
            _info('New book_set_key already exist. Merging with existing key.')
            updated_user_set_key = redis.hget(tracking_set_key, value)
        else:
            _info('New book_set_key does not exist. Creating new key.')
            USER_SET_ID_COUNTER = '{}:user_set_id_counter'.format(tracking_set_key)
            user_set_id = redis.incr(USER_SET_ID_COUNTER)
            updated_user_set_key = '{}:{}:user_set{}'.format(field, value, user_set_id)
            _info('Creating hset={} key={} value={}', tracking_set_key, value, updated_user_set_key)
            redis.hset(tracking_set_key, value, updated_user_set_key)

        # Update user_set_key name
        _info('Adding set={} book_id={}', updated_user_set_key, user_id)
        redis.sadd(updated_user_set_key, user_id)
        # Update tracking set value.
        _info('Updating hset={} key={} value={}', tracking_set_key, value, updated_user_set_key)
        redis.hset(tracking_set_key, value, updated_user_set_key)

        _info('Removing set={} user_id={}', user_set_key, user_id)
        redis.srem(user_set_key, user_id)
        if redis.scard(user_set_key) == 0:
            _info('Cleaning up user set={}', user_set_key)
            redis.delete(user_set_key)
            redis.hdel(tracking_set_key, old_value)

    _success('Edited user with isbn={} field={} value={}', username, field, value)


@cli.command()
@click.argument('entity', type=click.Choice(['book', 'user']))
@click.argument('key_type', type=click.Choice(['title', 'author', 'isbn', 'name', 'username', 'phone']))
@click.argument('keyword')
@config
def search(config: Config, entity: str, key_type: str, keyword: str):
    """
    Search for books.
    """
    redis = config.redis

    if entity == 'book':
        if key_type not in ['title', 'author', 'name', 'isbn']:
            _error('Not a valid entity:key_type combo')
            sys.exit(1)
        key_type_map = config.key_type_to_book_set_map
    else:
        if key_type not in ['name', 'username', 'phone']:
            _error('Not a valid entity:key_type combo')
            sys.exit(1)
        key_type_map = config.key_type_to_user_set_map

    # Get proper key to map to search.
    type_to_entity = key_type_map.get(key_type, None)

    # Get book_set_key
    _info('Using key={} to get entity set key', type_to_entity)
    if redis.hexists(type_to_entity, keyword):
        entity_set_key = redis.hget(type_to_entity, keyword)
        _info('Got entity set key {}', entity_set_key)
    else:
        _warn('{} with {} {} does not exist in library', entity, key_type, keyword)
        sys.exit(1)

    # Get book_entry_keys associated with this title.
    entity_ids = redis.smembers(entity_set_key)
    entities = []
    for entity_id in entity_ids:
        data = redis.hgetall(entity_id)
        if entity == 'user':
            user_loans_key = '{}:loans'.format(entity_id)
            data['loans'] = redis.hgetall(user_loans_key)
        entities.append(data)

    if entity == 'book':
        _display_list_of_books(entities)
    else:
        _display_list_of_users(entities)
    sys.exit(0)


@cli.command()
@click.argument('sort_by', type=click.Choice(['title', 'author', 'isbn', 'pages']))
@config
def sort_books_by(config: Config, sort_by: str):
    """
    Sort books.
    """
    redis = config.redis

    fields = ['title', 'author', 'isbn', 'pages']
    get_all_field_patterns = []
    pattern = ''
    for field in fields:
        field_pattern = '*->{}'.format(field)
        get_all_field_patterns.append(field_pattern)
        if field == sort_by:
            pattern = field_pattern

    sort_alphanumeric = sort_by != 'pages'
    books = redis.sort('books', alpha=sort_alphanumeric, by=pattern, get=get_all_field_patterns)
    results = []
    for i in range(0, len(books), 4):
        results.append({
            'title': books[i],
            'author': books[i + 1],
            'isbn': books[i + 2],
            'pages': books[i + 3]
        })
    _info('Sorted list of books by {}', sort_by)
    _display_list_of_books(results)
    sys.exit(0)


@cli.command()
@click.argument('username')
@click.argument('isbn')
@config
def checkout(config: Config, username: str, isbn: str):
    """
    Checkout a book with given isbn for the user with username
    """
    redis = config.redis
    key_type_to_user_map = config.key_type_to_user_set_map
    key_type_to_book_map = config.key_type_to_book_set_map

    if not _in_library(redis, username, key_type_to_user_map):
        _error('User {} does not exist in library', username)
        sys.exit(1)
    elif not _in_library(redis, isbn, key_type_to_book_map):
        _error('Book with isbn {} is not in library', key_type_to_book_map)
        sys.exit(1)

    user_set = _get_by_identifier(redis, username, key_type_to_user_map)
    book_set = _get_by_identifier(redis, isbn, key_type_to_book_map)
    for book_id in book_set:
        quantity = int(redis.hget(book_id, 'quantity'))
        if quantity > 0:
            for user_id in user_set:
                user_loans_key = '{}:loans'.format(user_id)
                redis.hincrby(user_loans_key, book_id, 1)
            _info('book {} now has quantity {}', book_id, quantity - 1)
            redis.hincrby(book_id, 'quantity', -1)
        else:
            _error('Book with isbn {} is not in stock', isbn)
            sys.exit(1)
    _success('Checkout completed')
    sys.exit(0)


@cli.command()
@click.argument('username')
@click.argument('isbn')
@config
def checkin(config: Config, username: str, isbn: str):
    """
    Return a checked out book with the given isbn
    for the user with the given username.
    """
    redis = config.redis
    key_type_to_user_map = config.key_type_to_user_set_map
    key_type_to_book_map = config.key_type_to_book_set_map

    if not _in_library(redis, username, key_type_to_user_map):
        _error('User {} does not exist', username)
        sys.exit(1)
    elif not _in_library(redis, isbn, key_type_to_book_map):
        _error('Book with isbn {} is not in library', key_type_to_book_map)
        sys.exit(1)

    user_set = _get_by_identifier(redis, username, key_type_to_user_map)
    book_set = _get_by_identifier(redis, isbn, key_type_to_book_map)
    for user_id in user_set:
        user_loans_key = '{}:loans'.format(user_id)
        for book_id in book_set:
            if redis.hexists(user_loans_key, book_id):
                loan_quantity = int(redis.hget(user_loans_key, book_id))
                loan_quantity -= 1
                if loan_quantity == 0:
                    _info('Returned all books with book_id {}', book_id)
                    _info('Deleting hset={} key={}', user_loans_key, book_id)
                    redis.hdel(user_loans_key, book_id)
                else:
                    _info('Book_id {} quantity is now {}', book_id, loan_quantity)
                    _info('Updating hset={} key={} value={}', user_loans_key, book_id, loan_quantity)
                    redis.hset(user_loans_key, book_id, loan_quantity)

                _info('Updating library stock hset={}', book_id)
                redis.hincrby(book_id, 'quantity', 1)


@cli.command()
@click.argument('username')
@config
def stat(config: Config, username: str):
    """
    Statistic on the user.
    """
    redis = config.redis
    key_type_to_user_map = config.key_type_to_user_set_map

    def display(loans):
        total = 0
        for book_id, quantity in loans.items():
            total += int(quantity)
            book_data = redis.hgetall(book_id)
            title = book_data.get('title')
            author = book_data.get('author')
            isbn = book_data.get('isbn')
            pages = book_data.get('pages')
            _success('book: title={} author={} isbn={} pages={} loaned={}', title, author, isbn, pages, quantity)
        _success('total loaned: {}', total)

    if not _in_library(redis, username, key_type_to_user_map):
        _error('User {} does not exist', username)
        sys.exit(1)

    user_set = _get_by_identifier(redis, username, key_type_to_user_map)
    for user_id in user_set:
        user_loans_key = '{}:loans'.format(user_id)
        user_loans = redis.hgetall(user_loans_key)

        display(user_loans)


def _in_library(redis: Redis, identifier: str, key_type_map: dict) -> bool:
    # Use uniqueness of isbn/username to determine existence in library
    if 'isbn' in key_type_map:
        identifier_to_set_key = key_type_map.get('isbn', 'isbn:book_set')
    elif 'username' in key_type_map:
        identifier_to_set_key = key_type_map.get('username', 'username:user_set')
    else:
        _error('Incompatible key_type_map {}', key_type_map)
        sys.exit(1)

    if redis.hexists(identifier_to_set_key, identifier):
        _warn('{} already exists', identifier)
        return True
    return False


def _get_by_identifier(redis: Redis, identifier: str, key_type_map: dict) -> set:
    if 'isbn' in key_type_map:
        identifier_set_key = key_type_map.get('isbn', 'isbn:book_set')
    elif 'username' in key_type_map:
        identifier_set_key = key_type_map.get('username', 'username:user_set')
    else:
        _error('Incompatible key_type_map {}', key_type_map)
        sys.exit(1)

    identifier_set = redis.hget(identifier_set_key, identifier)
    return redis.smembers(identifier_set)


def _display_list_of_books(books):
    """
    Print it out nicely.
    """
    for index, book in enumerate(books):
        title = book.get('title')
        author = book.get('author')
        isbn = book.get('isbn')
        pages = book.get('pages')
        quantity = book.get('quantity')
        _success('{}: title={} author={} isbn={} pages={} quantity={}', index, title, author, isbn, pages, quantity)


def _display_list_of_users(users):
    """
    Print it out nicely.
    """
    for index, user in enumerate(users):
        name = user.get('name')
        username = user.get('username')
        phone = user.get('phone')
        loans = user.get('loans')
        _success('{}: name={} username={} phone={} loans={}', index, name, username, phone, loans)


@cli.command()
@click.argument('arguments', nargs=-1, required=False)
def echo(arguments: tuple):
    """
    Echo arguments back.
    """
    click.secho(' '.join(arguments), fg='yellow')


def _success(format_string: str, *args):
    """
    Helper method to stylistically print success level logs.
    """
    __display(format_string.format(*args), 'green')


def _info(format_string: str, *args):
    """
    Helper method to stylistically print info level logs.
    """
    __display(format_string.format(*args), 'blue')


def _warn(format_string: str, *args):
    """
    Helper method to stylistycally print warning level logs.
    """
    __display(format_string.format(*args), 'yellow')


def _error(format_string: str, *args):
    """
    Helper method to stylistically print error level logs.
    """
    __display(format_string.format(*args), 'red')


def __display(message: str, color: str):
    """
    Display message with color
    """
    click.secho(message, fg=color)


if __name__ == '__main__':
    cli()
