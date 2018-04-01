class Config(object):
    """
    Class container used to pass into Click decorators.
    This class should be used to pass configurations flags.
    """
    def __init__(self):
        self.verbose = False
        self.redis = None
        self.all_books_key = None
        self.key_type_to_book_set_map = None
        self.key_type_to_user_set_map = None
