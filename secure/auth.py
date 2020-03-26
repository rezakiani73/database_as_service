import psycopg2
from passlib.hash import pbkdf2_sha256

conn_string = "host='localhost' dbname='dbas' user='DBAS' password='DBAS'"
conn = psycopg2.connect(conn_string)
cursor = conn.cursor()


def auth_user(username, password, key_space=''):
    cursor.execute("select * from users where username='%s';" % (username,))
    if cursor.rowcount == 1:
        memory = cursor.fetchone()
        return pbkdf2_sha256.verify(password, memory[2])
    return False


def create_user(username, password):
    hashed_password = pbkdf2_sha256.encrypt(password, rounds=100, salt_size=16)
    cursor.execute("insert into users (username, password) values ('%s', '%s');" % (username, hashed_password))
    conn.commit()


def create_info_dbs():
    cursor.execute(
        'CREATE TABLE user_dbs(ID SERIAL, USERNAME TEXT, DATABASE TEXT, INSERT_num INT DEFAULT 0, SELECT_num INT DEFAULT 0, DELETE_num INT DEFAULT 0, UPDATE_num INT DEFAULT 0,SUM INT DEFAULT 0);')
    conn.commit()


def insert_UserDB_info(username, database_name):
    cursor.execute("insert into user_dbs (username, database)  values('%s', '%s');" % (username, database_name))
    conn.commit()


def return_users_databases(username):
    cursor.execute(
        "select database,insert_num,select_num,delete_num,update_num,(insert_num+select_num+delete_num+update_num) as total,(insert_num+select_num+delete_num+update_num)*12 as cost from user_dbs WHERE username = '%s'" % (
            username))
    if cursor.rowcount >= 1:
        results = cursor.fetchall()
        return results

    else:
        return "false"


def dbs_name(username):
    cursor.execute("select database from user_dbs WHERE username = '%s'" % (username))
    if cursor.rowcount >= 1:
        results = cursor.fetchall()
        result_of_db = [str(d[0]) for d in results]
        return result_of_db
    else:
        return "false"


def update_operatins_numbers(db_name, col):
    cursor.execute("update user_dbs set %s=%s+1 where database='%s';" % (col, col, db_name))
    conn.commit()


def chart_doughnut_items(username):
    cursor.execute(
        "select sum(insert_num) as T_in ,sum(select_num) as T_sel, sum(delete_num) as T_del,sum(update_num) as T_up,(sum(insert_num)+sum(select_num)+sum(delete_num)+sum(update_num)) as total from user_dbs where username='%s';" % (
        username))
    results = cursor.fetchall()
    return results
def pay_faunction(username):
    cursor.execute("update user_dbs set insert_num=0,select_num=0,delete_num=0,update_num=0 where username='%s';" %(username))
    conn.commit()