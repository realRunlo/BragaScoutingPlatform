import json
import os
import logging
import sys
from MySQLdb import _mysql


class Db_handler:
    '''Class to handle mySql database connections'''

    db_config = None
    connection = None
    logger = None

    def __init__(self,config:dict=None,config_json:str=None,logger:logging.Logger=None) -> None:
        if logger:
            self.logger = logger
        if config:
            self.db_config = config
        elif config_json:
            if os.path.exists(config_json):
                self.db_config = json.load(open(config_json, 'r'))
                self.log(f'Loaded config file {config_json}')
            else:
                self.log(f'Config file {config_json} not found',logging.ERROR)
        else:
            self.log('No config provided',logging.ERROR)



    def create_connection(self):
        """Creates a connection to the MySQL database"""
        try:
            self.connection = _mysql.connect(**self.db_config)
            self.log('Connection to the database established')
        except Exception as e:
            self.connection = None
            self.log('Error creating connection to the database',logging.ERROR)
            self.log(e,logging.ERROR)


    def insert(self,table:str, values:str):
        """Inserts values into a table"""
        if self.connection:
            self.log(f'''Query: INSERT INTO scouting.{table} VALUES {values}''')
            try:
                self.connection.query(f"""INSERT INTO scouting.{table} VALUES {values}""")
                self.connection.commit()
                self.log(f'Values {values} inserted into table {table}')
            except Exception as e:
                self.log(f'Error inserting values {values} into table {table}\n{e}',logging.ERROR)

    def insert_or_update(self,table:str, values:str,on_update:str='',parameters:str=''):
        """Inserts/updates values into a table"""
        if self.connection:
            #print(f'''INSERT INTO scouting.{table} {parameters} VALUES {values} ON DUPLICATE KEY UPDATE {on_update}''')
            self.log(f'''Query: INSERT INTO scouting.{table} {parameters} VALUES {values} ON DUPLICATE KEY UPDATE {on_update}''')
            try:
                query = f'''INSERT INTO scouting.{table} {parameters} VALUES {values} as new'''
                if on_update != '':
                    query += f' ON DUPLICATE KEY UPDATE {on_update}'
                self.connection.query(query)
                self.connection.commit()
                self.log(f'Values {values} inserted/updated into table {table}')
            except Exception as e:
                self.log(f'Error inserting/updating values {values} into table {table}\n{e}',logging.ERROR)
                open('error.txt','w').write(query)
                sys.exit()


    def insert_or_update_many(self,table:str, values:list[str],on_update:str='',parameters:str='',batch_size:int=500):
        """Inserts/updates values into a table in batches"""
        if self.connection:
            self.log(f'''Query: Inserting multiple values into scouting.{table}''')
            try:
                batch = ','.join(values[0:batch_size])
                # reduce batch_size if query is bigger than 0.7 MB
                while len(batch.encode('utf-8')) > 700000:
                    batch_size = int(batch_size/2)
                    batch = ','.join(values[0:batch_size])
                print(f'batch_size: {batch_size}')
                i = 0
                while i < len(values):
                    batch = ','.join(values[i:i+batch_size])
                    query = f'''INSERT INTO scouting.{table} {parameters} VALUES {batch} as new'''
                    if on_update != '':
                        query += f' ON DUPLICATE KEY UPDATE {on_update}'
                    self.connection.query(query)
                    self.connection.commit()
                    i += batch_size
                self.log(f'Values inserted/updated into table {table}')
            except Exception as e:
                self.log(f'Error inserting/updating values into table {table}\n',logging.ERROR)
                self.log(e,logging.ERROR)
                open('error.txt','w').write(query)
                sys.exit()
    
    def insert_or_update_many_union(self,table:str, values:list[str],on_update:str='',parameters:str='',batch_size:int=500):
        """Inserts/updates values into a table in batches using union all to connect values"""
        if self.connection:
            self.log(f'''Query: Inserting multiple values into scouting.{table} (UNION ALL)''')
            try:
                batch = ' UNION ALL '.join(values[0:batch_size])
                # reduce batch_size if query is bigger than 0.7 MB
                while len(batch.encode('utf-8')) > 700000:
                    batch_size = int(batch_size/2)
                    batch = ' UNION ALL '.join(values[0:batch_size])
                i = 0
                while i < len(values):
                    batch = ' UNION ALL '.join(values[i:i+batch_size])
                    query = f'''INSERT INTO scouting.{table} {parameters} {batch}'''
                    if on_update != '':
                        query += f' ON DUPLICATE KEY UPDATE {on_update}'
                    self.connection.query(query)
                    self.connection.commit()
                    i += batch_size
                self.log(f'Values inserted/updated into table {table}')
            except Exception as e:
                self.log(f'Error inserting/updating values into table {table}\n',logging.ERROR)
                self.log(e,logging.ERROR)
                open('error.txt','w').write(query)
                sys.exit()


    def close_connection(self):
        """Closes the connection to the MySQL database"""
        if self.connection:
            self.connection.close()
            self.log('Connection to the database closed')

    def log(self, message:str,level=logging.INFO):
        """Logs a message"""
        if self.logger:
            self.logger.log(level,message)
