from bs4 import BeautifulSoup
from string import ascii_lowercase
import urllib.request
from typing import List, Tuple
from dbmanager import DbManager
import datetime
import re

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

def get_player_stats(player_id: str, year: int = 2020, last_updated = None):
    assert year >= 2019 and year <= 2020
    assert len(player_id) > 1
    
    playerlog_lastfive = []

    url = BASKETBALL_REFERENCE_PLAYERS_BASE_URL + player_id[0] + "/" + player_id + "/gamelog/" + str(year)
    html = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(html, 'html.parser')

    player_game_log = soup.find('div', {'id': "all_pgl_basic"})
    player_game_log_row = player_game_log.find_all('tr', {"id": re.compile("^pgl_basic")})
    
    for row in range(-5,0):
        
        row_data_stat = player_game_log_row[row]
        
        data_tuple = []
        
        #for data in row_data_stat:
            #data_tuple.append(data.name('data_stat'))
        
        #playerlog_lastfive.append(data_tuple)

    #print (playerlog_lastfive)
    return playerlog_lastfive
    

# Game Log Columns
# *GameScore = Points + 1.2 * Rebounds + 1.5 * Assists + 3 * (Blocks + Steals) - Turnovers
# TeamGameNumber, PlayerGameNumber, Date, Team, Opponent, GameStarted, MinutesPlayed, FG, FGA, 3P, 3PA, FT, FTA, OffensiveRebounds, DefensiveRebounds, TotalRebounds, Assists, Steals, Blocks, Turnovers, Fouls, Points, PlusMinus, GameScore*
#region DB management

def table_exists(db_manager: DbManager, table_name: str) -> bool:
    table_query = "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{}}'".format(table_name)
    return int(db_manager.execute(table_query).fetchone()[0]) == 1

def players_table_exists(db_manager: DbManager) -> bool:
    return table_exists(db_manager, 'players')

def game_logs_table_exists(db_manager: DbManager) -> bool:
    return table_exists(db_manager, 'game_logs')

def create_players_table(db_manager: DbManager):
    sql_create_players_table = """
        CREATE TABLE IF NOT EXISTS players (
        id   TEXT PRIMARY KEY,
        name TEXT NOT NULL);
        """

    if db_manager.execute(sql_create_players_table) is None:
        print("Error creating table")

def create_game_logs_table(db_manager: DbManager):
    sql_create_game_logs_table = """
    CREATE TABLE IF NOT EXISTS game_logs (
    team_game_number INTEGER,
    player_game_number INTEGER,
    date INTEGER,
    team TEXT,
    opponent TEXT,
    game_started INTEGER,
    
    )
    """

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
    get_player_stats('jamesle01',2020)