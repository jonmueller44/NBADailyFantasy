from bs4 import BeautifulSoup
from string import ascii_lowercase
import urllib.request
from typing import List, Tuple

import sqlite3 #added for sql
from sqlite3 import Error #added for sql

PlayerInfo = Tuple[str, str]  # player_id, name
PlayerList = List[PlayerInfo]

BASKETBALL_REFERENCE_BASE_URL = "https://www.basketball-reference.com/"
BASKETBALL_REFERENCE_PLAYERS_BASE_URL = BASKETBALL_REFERENCE_BASE_URL + "players/"

def get_active_players_by_letter(letter: str) -> PlayerList:
    assert len(letter) == 1
    assert letter.isalpha()

    url = BASKETBALL_REFERENCE_PLAYERS_BASE_URL + letter
    html = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(html, 'html.parser')

    player_list = []
    
    table = soup.find('table')
    active_players_strong = table.find_all('strong')
    for strong in active_players_strong:
        player_name = strong.a.string
        player_id = strong.a.get("href")
        player_id = player_id[11:player_id.index('.')]
        player_list.append((player_id, player_name))
  
    return player_list

def get_active_players() -> PlayerList:
    player_list = []
    for letter in ascii_lowercase:
        player_list.extend(get_active_players_by_letter(letter))

    return player_list

#Daniel edit for sql code

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
    return conn

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def create_players_database():
    
    database = r"D:\\13-SQLite\\NBADailyFantasy\\NBADailyFantasy.db" #might need another path for jon
    
    sql_create_players_table = """ CREATE TABLE IF NOT EXISTS players (
        id integer PRIMARY KEY,
        name text NOT NULL, 
        href text NOT NULL
        ); """
        
    # create a database connection
    conn = create_connection(database)

    # create tables
    if conn is not None:
        # create projects table
        create_table(conn, sql_create_players_table)

    else:
        print("Error! cannot create the database connection.")

def update_players_database():
    return

#end Daniel edits

#print(get_active_players()) #Daniel modified this line to test for all players, it took about 30 seconds