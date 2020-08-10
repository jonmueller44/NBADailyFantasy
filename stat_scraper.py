from bs4 import BeautifulSoup
from string import ascii_lowercase
import urllib.request
from typing import List, Tuple
from dbmanager import DbManager

PlayerInfo = Tuple[str, str]  # player_id, name
PlayerList = List[PlayerInfo]

NBA_DB = "nba.db"
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

def create_players_database():
    dbManager = DbManager(NBA_DB)

    sql_create_players_table = """
        CREATE TABLE IF NOT EXISTS players (
        id   text PRIMARY KEY,
        name text NOT NULL); """

    if dbManager.execute(sql_create_players_table) is None:
        print("Error creating table")

def update_players_database():
    return


if __name__ == '__main__':
    #print(get_active_players())
    create_players_database()