import json


class Table:
    def __init__(self, name, connection=None):
        self.name = name
        self.columns = []
        self.connection = connection

    def get_columns(self):
        return self.columns

    def insert_column(self, column):
        self.columns.append(column)

    def send_message(self, message):
        self.connection.client.send(json.dumps(message).encode())
        result = json.loads(self.connection.client.recv(2048).decode())
        return result

    def delete(self):
        message = {'operation': 'drop table', 'name': self.name}
        return self.send_message(message)

    def put_item(self, items):
        message = {'operation': 'insert into', 'name': self.name, 'items': items}
        return self.send_message(message)

    def get_item(self, columns=None):
        message = {'operation': 'select', 'name': self.name, 'columns': columns}
        return self.send_message(message)

    def update_item(self, items, keys):
        message = {'operation': 'update', 'name': self.name, 'items': items, 'keys': keys}
        return self.send_message(message)

    def delete_item(self, keys):
        message = {'operation': 'delete', 'name': self.name, 'keys': keys}
        return self.send_message(message)
