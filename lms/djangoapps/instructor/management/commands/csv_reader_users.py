import csv
import sys
import MySQLdb
from datetime import datetime
from django.db import connection

cur = connection.cursor()

def update_users_table():

    users_csv = open("/home/ubuntu/SGU_Banner/users.csv", 'r')

    cur = connection.cursor()

    cur.execute("TRUNCATE sgu_users")

    try:
        reader = csv.reader(users_csv)
        for row in reader:
            if row:
                date_time = str(datetime.now())
                cur.execute("""INSERT INTO sgu_users(sgu_username, sgu_email, sgu_anumber, last_updated) VALUES(%s, %s, %s, %s)""", (row[0],row[3],row[7],date_time))
    except Exception,e:
        print e
    finally:
        users_csv.close()
