class User(object):
    def __init__(self, name: str, username: str, phone: int):
        self.name = name
        self.username = username
        self.phone = phone

    def __repr__(self):
        return 'User(name={}, username={}, phone={})'.format(self.name, self.username, self.phone)
