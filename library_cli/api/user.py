class User(object):
    def __init__(self, name: str, username: str, phone: int):
        self.name = name
        self.username = username
        self.phone = phone
        self.borrowing = []
        self.id = None

    def __repr__(self):
        return 'User(id={}, name={}, username={}, phone={}, borrowing={})'.format(self.id,
                                                                                  self.name,
                                                                                  self.username,
                                                                                  self.phone,
                                                                                  self.borrowing)
