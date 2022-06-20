import logging
import sqlite3 as sl
from datetime import datetime

# TODO: Add documentation to this class
class Database:
    NULL = ''
    
    def __init__(self, file='places.db') -> None:
        self.con = sl.connect(file)
        
        self.tables = {
            'RESTAURANT': """
                          id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                          timestamp TEXT,
                          name TEXT,
                          location TEXT,
                          rating FLOAT,
                          prange INT
                          """
        }
        
        self._create_all_tables()
        
    def _get_table_columns_list(self, table_name: str):
        return [entry.lstrip().rstrip().split(' ')[0] for entry in self.tables[table_name].split(',')]
    
    def _get_table_columns_tuple_string(self, table_name: str):
        names = self._get_table_columns_list(table_name)
        return '(' + ','.join(names) + ')'
    
    def _create_table(self, table_name: str):
        with self.con:
            # Create table if not present already
            self.con.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({self.tables[table_name]});")
            
    def _create_all_tables(self):
        with self.con:
            for table in self.tables.keys():
                self._create_table(table)
    
    def is_table_empty(self, table_name: str):
        with self.con:
            resulting_cursor = self.con.execute(f"SELECT count(*) FROM {table_name}")
            count = [r for r in resulting_cursor][0][0]
            return False if count > 0 else True
    
    # TODO: Add table multiple entries at once with executemany()
    def add_table_entry(self, table_name: str, **kwargs):
        command = f"INSERT OR IGNORE INTO {table_name} {self._get_table_columns_tuple_string(table_name)} VALUES ("
        
        entry_name = self._get_table_columns_list(table_name)
        entry_order_dict = {}
        
        for i, ename in enumerate(entry_name):
            entry_order_dict[ename] = i
        
        if len(entry_name) != len(kwargs.keys()):
            logging.error(f'add_table_entry() failed for table: {table_name}')
            logging.error(f'Reason: table requires {len(entry_name)} entries but {len(kwargs.keys())} were supplied')
            return
        
        entries = [None] * len(entry_name)
        for k, v in kwargs.items():
            v_toadd = ''
            if isinstance(v, str):
                v_toadd = f"\'{v}\'"
                if not v:
                    v_toadd = "NULL"
                elif v.startswith('_'):
                    v_toadd = f'{v[1:]}'
            else:
                v_toadd = f'{v}'
            entries[entry_order_dict[k]] = v_toadd

        command += ','.join(entries) + ')'
        
        with self.con:
            self.con.execute(command)
            
    def get_table_entries_by_values(self, table_name: str, operator='=', **kwargs):
        command = f"SELECT * FROM {table_name} WHERE "
        entries = []
        
        for k, v in kwargs.items():
            v_toadd = f'{k} {operator} '
            if isinstance(v, str):
                v_toadd += f"\'{v}\'"
                if not v:
                    v_toadd += "NULL"
            else:
                v_toadd += f'{v}'
            entries.append(v_toadd)
            
        command += ' AND '.join(entries) + ';'
        
        with self.con:
            return [r for r in self.con.execute(command)]
    
    def add_restaurant_entry(self, name: str, location: str, rating: float, price_range: int):
        self.add_table_entry('RESTAURANT', id=Database.NULL, name=name, rating=rating, prange=price_range, timestamp=str(datetime.now()), location=location)
    
    def get_restaurant_by_name(self, name: str, location: str):
        return self.get_table_entries_by_values('RESTAURANT', operator='=', name=name, location=location)
    