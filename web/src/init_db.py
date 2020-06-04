# Import MySQL Connector Driver
import mysql.connector as mysql
import json

# Load the credentials from the secured .env file
import os
from dotenv import load_dotenv
load_dotenv('credentials.env')

# For timestamps
from datetime import datetime

db_user = os.environ['MYSQL_USER']
db_pass = os.environ['MYSQL_PASSWORD']
db_name = os.environ['MYSQL_DATABASE']
db_host = os.environ['MYSQL_HOST'] # must 'localhost' when running this script outside of Docker

# Connect to the database
db = mysql.connect(host=db_host, database=db_name, user=db_user, password=db_pass)
cursor = db.cursor()

# Create table (wrapping it in a try-except is good practice)
#cursor.execute("drop table if exists users;")
try:
  cursor.execute("""
    CREATE TABLE Users (
      id          integer AUTO_INCREMENT PRIMARY KEY,
      first_name  VARCHAR(30) NOT NULL,
      last_name   VARCHAR(30) NOT NULL,
      email       VARCHAR(50) NOT NULL,
      password    VARCHAR(20) NOT NULL,
      created_at  TIMESTAMP
    );
  """)
  #Insert Records
  query = "insert into Users (first_name, last_name, email, password, created_at) values (%s, %s, %s, %s, %s)"
  values = [
     ('Jerry','Chen','jerryjchen98@gmail.com', 'Lorddeathray92*=', datetime.now()),
     ('ramsin', 'khoshabeh', 'ramsin@khoshabeh.com', 'abc123', datetime.now())
  ]
  cursor.executemany(query, values)
  db.commit()
except:
  print("Users Table already exists. Not recreating it.")

cursor = db.cursor()
try:
  cursor.execute("""
    CREATE TABLE Visit_Count (
      id          integer AUTO_INCREMENT PRIMARY KEY,
      route_name  VARCHAR(30) NOT NULL,
      visit_count VARCHAR(30) NOT NULL
    );
  """)
  #Insert Records
  query = "insert into Visit_Count (route_name, visit_count) values (%s, %s)"
  values = [
     ('/about', '0'),
     ('/admin','0'),
     ('/home','0'),
     ('/login','0'),
     ('/pricing','0'),
     ('/product','0'),
     ('/register','0')
  ]
  cursor.executemany(query, values)
  db.commit()
except:
  print("Visit_Count Table already exists. Not recreating it.")

cursor = db.cursor()
try:
  cursor.execute("""
    CREATE TABLE Visits (
      id          integer AUTO_INCREMENT PRIMARY KEY,
      session_id  VARCHAR(30) NOT NULL,
      route_name  VARCHAR(30) NOT NULL,
      timestamp   TIMESTAMP
    );
  """)
  db.commit()
except:
  print("Visits Table already exists. Not recreating it.")

# Selecting User Records
cursor.execute("select * from Users;")
print('---------- DATABASE INITIALIZED ----------')
[print(x) for x in cursor]

# Selecting Visits Records
cursor.execute("select * from Visit_Count;")
print('---------- DATABASE INITIALIZED ----------')
[print(x) for x in cursor]

# Selecting Visits Records
cursor.execute("select * from Visits;")
print('---------- DATABASE INITIALIZED ----------')
[print(x) for x in cursor]
db.close()
