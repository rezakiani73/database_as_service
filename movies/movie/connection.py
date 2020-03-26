from . import Table
import socket
import json


class Connection:
    def __init__(self, username, password, url, port):
        self.client = socket.socket()
        address = (url, port)
        self.client.connect(address)
        self.client.send((username + " " + password).encode())
        message_from_server = self.client.recv(2048)
        if message_from_server.decode() == 'False':
            self.client.send('exit'.encode())
            self.status = False
        else:
            self.status = True

    def send_message(self, message):
        self.client.send(json.dumps(message).encode())
        result = self.client.recv(2048)
        data = json.loads(result.decode())
        return data

    def use_database(self, database):
        message = {'operation': 'use database', 'database': database}
        return self.send_message(message)

    def get_databases(self):
        message = {'operation': 'show databases'}
        return self.send_message(message)

    def get_tables(self):
        message = {'operation': 'show tables'}
        data = self.send_message(message)
        tables = []
        for row in data:
            new_table = Table.Table(row['name'])
            for column in row['columns']:
                new_table.insert_column(column)
            tables.append(new_table)
        return tables

    def insert_db_info(self,username,database_name):
        message = {'operation': 'insert_to_usersdb_info', 'username': username, 'database_name':database_name}
        return self.send_message(message)

    def payment_action(self,username):
        message = {'operation': 'payment the price', 'username': username}
        return self.send_message(message)


    def return_user_dbs(self,username):
        message = {'operation': 'return user dbs', 'username': username}
        data=self.send_message(message)
        return data
    def chart_doughnut(self,username):
        message = {'operation': 'return chart_doughnut items', 'username': username}
        return self.send_message(message)

    def create_db_info(self):
        message = {'operation': 'create user database information'}
        return self.send_message(message)

    def create_database(self, database):
        message = {'operation': 'create database', 'database': database}
        return self.send_message(message)

    def delete_database(self, database):
        message = {'operation': 'delete database', 'database': database}
        return self.send_message(message)

    def create_table(self, name, columns, primary_keys):
        message = {'operation': 'create table', 'name': name, 'columns': columns, 'primary_keys': primary_keys}
        return self.send_message(message)

    def create_user(self, username, password):
        message = {'operation': 'create user', 'username': username, 'password': password}
        return self.send_message(message)

    def table(self, name):
        message = {'operation': 'get table', 'name': name}
        result = self.send_message(message)
        new_table = Table.Table(result['name'], self)
        for column in result['columns']:
            new_table.insert_column(column)
        return new_table

    def close_connection(self):
        message = {'operation': 'exit'}
        self.client.send(json.dumps(message).encode())
        self.client.close()
