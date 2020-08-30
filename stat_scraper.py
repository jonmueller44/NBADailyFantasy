from bs4 import BeautifulSoup
from string import ascii_lowercase
import urllib.request
from typing import List, Tuple, Any
from dbmanager import DbManager
import datetime
import re
import time

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

def sanitize_player_stats(stats: List[str], player_id: str, season: int, is_playoffs: bool = False) -> Tuple[Any]:
    sanitized_stats = []
    idx = 0
    # player_id
    sanitized_stats.append(player_id)
    # team_game_number, player_game_number
    sanitized_stats.extend([int(stat) for stat in stats[:2]])
    # is_playoffs
    sanitized_stats.append(1 if is_playoffs else 0)
    # season, date
    ymd = [int(val) for val in stats[2].split('-')]
    sanitized_stats.append(season)
    sanitized_stats.append(datetime.date(ymd[0], ymd[1], ymd[2]))
    # team
    sanitized_stats.append(stats[4])
    # at_home
    if stats[5] == '@':
        sanitized_stats.append(0)
        idx = 6
    else:
        sanitized_stats.append(1)
        idx = 5
    # opponent
    sanitized_stats.append(stats[idx])
    # game_started
    idx += 2
    sanitized_stats.append(int(stats[idx]))
    # seconds_played
    idx += 1
    minutes_played = [int(val) for val in stats[idx].split(':')]
    sanitized_stats.append(minutes_played[0] * 60 + minutes_played[1])
    # field_goals/field_goal_attempts, three_points/three_point_attempts, free_throws/free_throw_attempts
    for _ in range(3):
        idx += 1
        sanitized_stats.append(int(stats[idx]))

        idx += 1
        attempts = int(stats[idx])
        sanitized_stats.append(attempts)
        if attempts > 0:
            idx += 1
    # offensive_rebounds
    idx += 1
    sanitized_stats.append(int(stats[idx]))
    # defensive_rebounds
    idx += 1
    sanitized_stats.append(int(stats[idx]))
    idx += 1 # skip total rebounds
    # assists, steals, blocks, turnovers, fouls, points
    for i in range(idx + 1, idx + 7, 1):
        sanitized_stats.append(int(stats[i]))
    # plus_minus
    idx += 8
    sanitized_stats.append(0 if idx >= len(stats) else int(stats[idx]))
    # fanduel_score
    fanduel_score = sanitized_stats[-2] + 1.2 * (sanitized_stats[-8] + sanitized_stats[-9]) + 1.5 * sanitized_stats[-7] + 3 * (sanitized_stats[-5] + sanitized_stats[-6]) - sanitized_stats[-4]
    sanitized_stats.append(fanduel_score)

    return tuple(sanitized_stats)

def get_player_stats(player_id: str, year: int = 2020, last_updated: str = '') -> List[Tuple[Any]]:
    assert year >= 2019 and year <= 2020
    assert len(player_id) > 1
    
    player_game_logs = []

    url = BASKETBALL_REFERENCE_PLAYERS_BASE_URL + player_id[0] + "/" + player_id + "/gamelog/" + str(year)
    html = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(html, 'html.parser')

    player_game_log = soup.find('div', {'id': "all_pgl_basic"})
    if player_game_log is None:
        return player_game_logs
    player_game_log_rows = player_game_log.find_all('tr', {"id": re.compile("^pgl_basic")})
    
    for game_log in player_game_log_rows:
        game_stats = []
        for stat in game_log.strings:
            game_stats.append(stat)
        
        player_game_logs.append(sanitize_player_stats(game_stats, player_id, year))

    return player_game_logs
    

#region DB management
# Game Log Columns
# fanduel_score = points + 1.2 * rebounds + 1.5 * assists + 3 * (blocks + steals) - turnovers
# player_id, team_game_number, player_game_number, is_playoffs, season, date, team, at_home, opponent, game_started, seconds_played, field_goals, field_goal_attempts, three_points, three_point_attempts, free_throws, free_throw_attempts, offensive_rebounds, defensive_rebounds, assists, steals, blocks, turnovers, fouls, points, plus_minus, fanduel_score

def table_exists(db_manager: DbManager, table_name: str) -> bool:
    table_query = "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{}'".format(table_name)
    return int(db_manager.execute(table_query).fetchone()[0]) == 1

def players_table_exists(db_manager: DbManager) -> bool:
    return table_exists(db_manager, 'Players')

def game_logs_table_exists(db_manager: DbManager) -> bool:
    return table_exists(db_manager, 'GameLogs')

def last_updated_table_exists(db_manager: DbManager) -> bool:
    return table_exists(db_manager, 'LastUpdated')

def create_players_table(db_manager: DbManager):
    sql_create_players_table = """
        CREATE TABLE IF NOT EXISTS Players (
        id   TEXT PRIMARY KEY,
        name TEXT NOT NULL);
        """

    if db_manager.execute(sql_create_players_table) is None:
        print("Error creating Players table.")

def create_game_logs_table(db_manager: DbManager):
    sql_create_game_logs_table = """
    CREATE TABLE IF NOT EXISTS GameLogs (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id            TEXT,
    team_game_number     INTEGER,
    player_game_number   INTEGER,
    is_playoffs          INTEGER,
    season               INTEGER,
    date                 DATE,
    team                 TEXT,
    at_home              INTEGER,
    opponent             TEXT,
    game_started         INTEGER,
    seconds_played       INTEGER,
    field_goals          INTEGER,
    field_goal_attempts  INTEGER,
    three_points         INTEGER,
    three_point_attempts INTEGER,
    free_throws          INTEGER,
    free_throw_attempts  INTEGER,
    offensive_rebounds   INTEGER,
    defensive_rebounds   INTEGER,
    assists              INTEGER,
    steals               INTEGER,
    blocks               INTEGER,
    turnovers            INTEGER,
    fouls                INTEGER,
    points               INTEGER,
    plus_minus           INTEGER,
    fanduel_score        REAL) """

    if db_manager.execute(sql_create_game_logs_table) is None:
        print("Error creating GameLogs table.")

def create_last_updated_table(db_manager: DbManager):
    sql_create_last_updated_table = """
        CREATE TABLE IF NOT EXISTS LastUpdated (
        date   TEXT);
        """

    if db_manager.execute(sql_create_last_updated_table) is None:
        print("Error creating LastUpdated table.")

def drop_last_updated_table(db_manager: DbManager):
    sql_drop_last_updated_table = 'DROP TABLE LastUpdated'
    if db_manager.execute(sql_drop_last_updated_table) is None:
        print("Error dropping LastUpdated table.")

def get_player_ids(db_manager: DbManager) -> PlayerIds:
    get_ids_query = 'SELECT id FROM Players'
    result = db_manager.execute(get_ids_query)
    player_ids = []
    if result is not None:
        player_ids = [player_id[0] for player_id in result.fetchall()]
    
    return player_ids

def get_last_updated(db_manager: DbManager):
    get_date_query = 'SELECT date FROM LastUpdated'
    return db_manager.execute(get_date_query)     

def insert_player(db_manager: DbManager, player_info_tuple: PlayerInfo):
    insert_player_query = 'INSERT INTO Players (id,name) VALUES (?, ?)'
    db_manager.execute(insert_player_query, player_info_tuple)

def insert_game_log(db_manager: DbManager, game_log_tuple: Tuple[Any]):
    insert_game_log_query = 'INSERT INTO GameLogs VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    db_manager.execute(insert_game_log_query, game_log_tuple)
#endregion

def update_last_updated():
    db_manager = DbManager(NBA_DB)
    if not last_updated_table_exists(db_manager):
        create_last_updated_table(db_manager)
    else:
        drop_last_updated_table(db_manager)   

    insert_last_updated_query = 'INSERT INTO LastUpdated (id) VALUES (?)'
    db_manager.execute(insert_last_updated_query, datetime.datetime.now())


def update_players_table():
    db_manager = DbManager(NBA_DB)
    
    existing_player_ids = set()
    if not players_table_exists(db_manager):
        create_players_table(db_manager)
    else:
        existing_player_ids.update(get_player_ids(db_manager))
    
    if not game_logs_table_exists(db_manager):
        create_game_logs_table(db_manager)

    active_players = get_active_players()
    for player in active_players:
        time.sleep(1)
        player_id = player[0]
        print(player_id)
        if not player_id in existing_player_ids:
            insert_player(db_manager, player)
    
        stats = get_player_stats(player_id, 2020)
        for game_log in stats:
            insert_game_log(db_manager, game_log)

            


if __name__ == '__main__':
    update_players_table()