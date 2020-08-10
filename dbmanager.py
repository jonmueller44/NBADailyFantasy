import sqlite3
from typing import Tuple, Any

class DbManager():
    def __init__(self, db: str):
        try:
            self.connection = sqlite3.connect(db)
        except sqlite3.Error as e:
            print(e)
            self.connection = None
        self.cursor = self.connection.cursor()

    def __del__(self):
        self.connection.close()

    def execute(self, sql: str, args: Tuple[Any, ...] = None):
        try:
            if args is None:
                self.cursor.execute(sql)
            else:
                self.cursor.execute(sql, args)
            
            self.connection.commit()
        except sqlite3.Error as e:
            print(e)
            return None
        
        return self.cursor
        
