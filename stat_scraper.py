from bs4 import BeautifulSoup
from string import ascii_lowercase
import urllib.request
from typing import List, Tuple
from dbmanager import DbManager

PlayerInfo = Tuple[str, str]  # player_id, name
PlayerList = List[PlayerInfo]
PlayerIds  = List[str]

NBA_DB = "nba.db"
BASKETBALL_REFERENCE_BASE_URL = "https://www.basketball-reference.com/"
BASKETBALL_REFERENCE_PLAYERS_BASE_URL = BASKETBALL_REFERENCE_BASE_URL + "players/"

#region Scraping
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

def get_player_stats(player_id: str, year: int = 2020):
    assert year >= 2019 and year <= 2020
    assert len(player_id) > 1
    #
    #url = BASKETBALL_REFERENCE_PLAYERS_BASE_URL + player_id[0] + "/" + player_id + "/gamelog/" + str(year)


#region DB management
def players_table_exists(db_manager: DbManager) -> bool:
    player_table_query = "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='players'"
    return int(db_manager.execute(player_table_query).fetchone()[0]) == 1

def create_players_table(db_manager: DbManager):
    sql_create_players_table = """
        CREATE TABLE IF NOT EXISTS players (
        id   text PRIMARY KEY,
        name text NOT NULL); """

    if db_manager.execute(sql_create_players_table) is None:
        print("Error creating table")

def get_player_ids(db_manager: DbManager) -> PlayerIds:
    get_ids_query = 'SELECT id FROM players'
    result = db_manager.execute(get_ids_query)
    player_ids = []
    if result is not None:
        player_ids = [player_id[0] for player_id in result.fetchall()]
    
    return player_ids

def insert_player(db_manager: DbManager, player_info_tuple: PlayerInfo):
    add_player_query = 'INSERT INTO players (id,name) VALUES (?, ?)'
    db_manager.execute(add_player_query, player_info_tuple)
#endregion


def update_players_table():
    db_manager = DbManager(NBA_DB)
    
    existing_player_ids = set()
    if not players_table_exists(db_manager):
        create_players_table(db_manager)
    else:
        existing_player_ids.update(get_player_ids(db_manager))

    active_players = get_active_players_by_letter('a')
    for player in active_players:
        player_id = player[0]
        if not player_id in existing_player_ids:
            insert_player(db_manager, player)


if __name__ == '__main__':
    update_players_table()