# -*- coding: utf8 -*-
import sqlite3
conn = sqlite3.connect('database.db')
c = conn.cursor()
c.execute('''CREATE TABLE databases
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
             name VARCHAR(100) NOT NULL,
             string TEXT NOT NULL,
             version VARCHAR(3),
             relevance BIT DEFAULT 1)''')
conn.commit()
c.execute('''CREATE TABLE schedule
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
             id_base INTEGER NOT NULL,
             time time,
             relevance BIT DEFAULT 1,
             FOREIGN KEY (id_base) REFERENCES databases(id))''')
conn.commit()
c.execute('''CREATE TABLE checks
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
             id_schedule INTEGER NOT NULL,
             check_date datetime,
             data VARCHAR(500),
             FOREIGN KEY (id_schedule) REFERENCES schedule(id))''')
conn.commit()
c.execute('''CREATE TABLE addresses
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
             address VARCHAR(500))''')
conn.commit()

# Bases
c.execute('''INSERT INTO databases (name, string, version, relevance)
          VALUES("name_of_base", 'connection_string', "V83", 1)''')
c.execute('''INSERT INTO databases (name, string, version, relevance)
          VALUES("name_of_base", 'connection_string', "V83", 1)''')
c.execute('''INSERT INTO databases (name, string, version, relevance)
          VALUES("name_of_base", 'connection_string', "V83", 1)''')

# Schedule
c.execute('''INSERT INTO schedule (id_base, time) VALUES(1, time("19:10:00"))''')
c.execute('''INSERT INTO schedule (id_base, time) VALUES(2, time("19:10:00"))''')
c.execute('''INSERT INTO schedule (id_base, time) VALUES(2, time("15:00:00"))''')
c.execute('''INSERT INTO schedule (id_base, time) VALUES(3, time("19:10:00"))''')

# Addresses
c.execute('''INSERT INTO addresses (address) VALUES("address")''')
conn.commit()

conn.close()
