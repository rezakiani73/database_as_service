import auth
import json
import Table
import threading
import status_checker
from pymongo import MongoClient
from bson.json_util import dumps
from cassandra.cluster import Cluster
from cassandra.query import dict_factory
now_db={}
status = {'cassandra': False, 'mongodb': False}
try:
    cluster = Cluster(['localhost'], port=9042)
    session = cluster.connect()
    session.row_factory = dict_factory
    status['cassandra'] = True
except:
    session = None
    status['cassandra'] = False

try:
    mongo_client = MongoClient(serverSelectionTimeoutMS=1000)
    mongo_client.server_info()
    status['mongodb'] = True
except:
    mongo_client = None
    status['mongodb'] = False

cassandra_connection_status = status['cassandra']
mongo_connection_status = status['mongodb']
print('Cassandra : %s' % cassandra_connection_status)
print('Mongo : %s' % mongo_connection_status)
status_checker_thread = threading.Thread(target=status_checker.check, args=(status,))
status_checker_thread.start()


def get_databases():
    if cassandra_connection_status:
        databases = list(cluster.metadata.keyspaces.keys())
        return databases
    elif mongo_connection_status:
        return mongo_client.database_names()


def get_tables(database):
    if cassandra_connection_status:
        tables = list(cluster.metadata.keyspaces[database].tables.keys())
        return tables
    elif mongo_connection_status:
        mongo_db = mongo_client[database]
        return mongo_db.collection_names()


def get_columns(database, table):
    columns = list(cluster.metadata.keyspaces[database].tables[table].columns.keys())
    return columns


def execute(client, session, query):
    result = session.execute(query)
    return result


def handler(client, addr):
    global cassandra_connection_status, mongo_connection_status, cluster, session, mongo_client
    database = None
    user_credientials = client.recv(2048).decode().split(' ')
    username = user_credientials[0]
    password = user_credientials[1]
    print('User : %s' % username)
    print('Pass : %s' % password)

    if auth.auth_user(username, password):
        auth_result = "True"
    else:
        auth_result = "False"
    client.send(auth_result.encode())

    while auth_result == 'True':
        try:
            message = json.loads(client.recv(2048).decode())
        except:
            break

        users_dbs = auth.dbs_name(username)

        operation = message['operation']
        if (cassandra_connection_status != status['cassandra']) and status['cassandra']:
            cluster = status_checker.get_cassandra_session()
            session = cluster.connect()
            session.row_factory = dict_factory
        cassandra_connection_status = status['cassandra']
        if (mongo_connection_status != status['mongodb']) and status['mongodb']:
            mongo_connection_status = status['mongodb']
        mongo_client = status_checker.get_mongodb_client()
        if operation == 'exit' or (not mongo_connection_status and not cassandra_connection_status):
            break



        elif operation == 'create database':
            database = message['database']
            if mongo_connection_status:
               try:
                    mongo_database = mongo_client[database]
               except:
                   client.send(json.dumps('%s already exist ' % database).encode())

            if cassandra_connection_status:
                try:
                    message = "CREATE KEYSPACE IF NOT EXISTS %s WITH replication = {'class': 'SimpleStrategy', 'replication_factor' : 1};" % database
                    session.execute(message)
                except:
                    client.send(json.dumps('%s already exist ' % database).encode())

            if mongo_connection_status or cassandra_connection_status:
                client.send(json.dumps('Create database %s Successful' % database).encode())
            else:
                client.send(json.dumps('Create database %s Failed' % database).encode())

        elif operation == 'delete database':
            database = message['database']
            if mongo_connection_status:
                mongo_client.drop_database(database)
            if cassandra_connection_status:
                if database in get_databases():
                    message = 'drop KEYSPACE IF EXISTS %s ;' % database
                    session.execute(message)
            if mongo_connection_status or cassandra_connection_status:
                client.send(json.dumps('Drop database %s Successful' % database).encode())
            else:
                client.send(json.dumps('drop database %s Failed' % database).encode())

        elif operation == 'use database':
            global now_db
            database = message['database']
            now_db['mydb']=database
            if mongo_connection_status:
                mongo_database = mongo_client[database]
            if cassandra_connection_status and database in get_databases():
                session.set_keyspace(database)
                client.send(json.dumps('Using Database : %s' % database).encode())



        elif operation == 'show databases':
            databases = get_databases()
            client.send(json.dumps(databases).encode())

        elif operation == 'show tables':
            tables = []
            for table in get_tables(database):
                new_table = Table.Table(table)
                if cassandra_connection_status:
                    for column in get_columns(database, table):
                        new_table.insert_column(column)
                tables.append(new_table.__dict__)
            client.send(json.dumps(tables).encode())

        elif operation == 'create table':
            name = message['name']
            columns = message['columns']
            primary_keys = message['primary_keys']
            if mongo_connection_status:
                try:
                    mongo_database.create_collection(name)
                except:
                    client.send(json.dumps('riiide').encode())
            if cassandra_connection_status:
                message = 'CREATE TABLE ' + name + ' ('
                for column in columns:
                    message += column + " " + columns[column] + ","
                if len(primary_keys) != 0:
                    message += "PRIMARY KEY(" + primary_keys[0]
                    for i in range(1, len(primary_keys)):
                        message += ', ' + primary_keys[i]
                    message += '));'
                else:
                    message += ');'
                session.execute(message)
            if mongo_connection_status or cassandra_connection_status:
                client.send(json.dumps('Create table %s Successful' % name).encode())
            else:
                client.send(json.dumps('Create table %s Failed' % name).encode())

        elif operation == 'get table':
            table_name = message['name']
            new_table = Table.Table(table_name)
            if mongo_connection_status:
                collection = mongo_database[table_name]
            if cassandra_connection_status and table_name in get_tables(database):
                for column in get_columns(database, table_name):
                    new_table.insert_column(column)
            client.send(json.dumps(new_table.__dict__).encode())

        elif operation == 'drop table':
            table_name = message['name']
            if mongo_connection_status:
                mongo_database.drop_collection(table_name)
            if cassandra_connection_status:
                execute(client, session, 'drop table IF EXISTS ' + str(table_name))
            if mongo_connection_status or cassandra_connection_status:
                client.send(json.dumps('Drop table %s Successful' % table_name).encode())
            else:
                client.send(json.dumps('Drop table %s Failed' % table_name).encode())

        elif operation == 'insert into':
            global now_db
            # if 'jamshidi_reza_sahana2' in users_dbs:
            if now_db:
                auth.update_operatins_numbers(now_db['mydb'],'insert_num')
                name = message['name']
                items = message['items']
                if mongo_connection_status:
                    collection.insert_one(dict(items))
                if cassandra_connection_status:
                    message = 'insert into ' + name + ' ('
                    counter = 0
                    for item in items.keys():
                        counter += 1
                        if counter == len(items.keys()):
                            message += item
                        else:
                            message += item + ','
                    message += ') values ('
                    counter = 0
                    for item in items.keys():
                        counter += 1
                        if type(items[item]) == str:
                            data = '\'' + items[item] + '\''
                        else:
                            data = items[item]
                        if counter == len(items.keys()):
                            message += str(data)
                        else:
                            message += str(data) + ','
                    message += ');'
                    execute(client, session, message)
                if mongo_connection_status or cassandra_connection_status:
                    client.send(json.dumps('Insert Successful').encode())
                else:
                    client.send(json.dumps('Insert Failed').encode())
            else:
                client.send(json.dumps('no database with this name...').encode())


        elif operation == 'select':
            global now_db
            if now_db['mydb'] in users_dbs:
                print ("yeeeeees")
                auth.update_operatins_numbers(now_db['mydb'],'select_num')
                name = message['name']
                columns = message['columns']
                if cassandra_connection_status:
                    message = 'select '
                    if columns == None:
                        message += '* '
                    else:
                        counter = 0
                        for column in columns:
                            counter += 1
                            if counter == len(columns):
                                message += column
                            else:
                                message += column + ','
                    message += ' from ' + name
                    result = execute(client, session, message)
                    temp_list = []
                    for row in result:
                        temp_list.append(row)
                    client.send(dumps(temp_list).encode())
                elif mongo_connection_status:
                    client.send(dumps(collection.find()).encode())
            else:
                print ("nooooooo")
                return False

        elif operation == 'update':
            global now_db
            # if 'jamshidi_reza_sahana2' in users_dbs:
            if now_db:
                auth.update_operatins_numbers(now_db['mydb'],'update_num')
                name = message['name']
                items = message['items']
                keys = message['keys']
                if mongo_connection_status:
                    collection.update_many(keys, {'$set': items})
                if cassandra_connection_status:
                    message = 'update ' + name + ' set '
                    counter = 0
                    for item in items:
                        counter += 1
                        if type(items[item]) == str:
                            data = '\'' + items[item] + '\''
                        else:
                            data = str(items[item])
                        if counter == len(items.keys()):
                            message += item + '=' + data
                        else:
                            message += item + '=' + data + ','
                    message += ' where '
                    counter = 0
                    for key in keys:
                        counter += 1
                        if type(keys[key]) == str:
                            data = '\'' + keys[key] + '\''
                        else:
                            data = str(keys[key])
                        if counter == len(keys.keys()):
                            message += key + '=' + data
                        else:
                            message += key + '=' + data + ' AND '
                    execute(client, session, message)
                if mongo_connection_status or cassandra_connection_status:
                    client.send(json.dumps('Update Successful').encode())
                else:
                    client.send(json.dumps('Update Failed').encode())

        elif operation == 'delete':
            global now_db
            # if 'jamshidi_reza_sahana2' in users_dbs:
            if now_db:
                auth.update_operatins_numbers(now_db['mydb'],'delete_num')
                name = message['name']
                keys = message['keys']
                if mongo_connection_status:
                    collection.delete_many(keys)
                if cassandra_connection_status:
                    message = 'delete from ' + name + ' where '
                    counter = 0
                    for key in keys:
                        counter += 1
                        if type(keys[key]) == str:
                            data = '\'' + keys[key] + '\''
                        else:
                            data = str(keys[key])
                        if counter == len(keys.keys()):
                            message += key + '=' + data
                        else:
                            message += key + '=' + data + ' AND '
                    execute(client, session, message)
                if mongo_connection_status or cassandra_connection_status:
                    client.send(json.dumps('Delete Successful').encode())
                else:
                    client.send(json.dumps('Delete Failed').encode())

        elif operation == 'create user':
            auth.create_user(message['username'], message['password'])
            client.send(json.dumps('Created User %s' % message['username']).encode())

        elif operation == 'create user database information':
            auth.create_info_dbs()
            client.send(json.dumps('Created User database information').encode())

        elif operation == 'insert_to_usersdb_info':
            auth.insert_UserDB_info(message['username'], message['database_name'])
            client.send(json.dumps('inserted User and database information').encode())

        elif operation == 'return user dbs':
            client.send(json.dumps(auth.return_users_databases(message['username'])).encode())

        elif operation == 'return chart_doughnut items':
            client.send(json.dumps(auth.chart_doughnut_items(message['username'])).encode())
        elif operation == 'payment the price':
            auth.pay_faunction(message['username'])
            client.send(json.dumps('your payment is done').encode())


    client.close()
