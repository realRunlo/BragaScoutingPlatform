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
        except:
            self.connection = None
            self.log('Error creating connection to the database',logging.ERROR)


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

    def insert_or_update(self,table:str, values:str,on_update:str,parameters:str=''):
        """Inserts/updates values into a table"""
        if self.connection:
            #print(f'''INSERT INTO scouting.{table} {parameters} VALUES {values} ON DUPLICATE KEY UPDATE {on_update}''')
            self.log(f'''Query: INSERT INTO scouting.{table} {parameters} VALUES {values} ON DUPLICATE KEY UPDATE {on_update}''')
            try:
                self.connection.query(f'''INSERT INTO scouting.{table} {parameters} VALUES {values} ON DUPLICATE KEY UPDATE {on_update}''')
                self.connection.commit()
                self.log(f'Values {values} inserted/updated into table {table}')
            except Exception as e:
                self.log(f'Error inserting/updating values {values} into table {table}\n{e}',logging.ERROR)


    def close_connection(self):
        """Closes the connection to the MySQL database"""
        if self.connection:
            self.connection.close()
            self.log('Connection to the database closed')

    def log(self, message:str,level=logging.INFO):
        """Logs a message"""
        if self.logger:
            self.logger.log(level,message)



############################## Test with players ##############################

# current_folder = os.path.dirname(os.path.abspath(__file__))

# db = DB(config_json=os.path.join(current_folder, 'db_config.json'))
# db.create_connection()
# print('Connection established' if db.connection else 'Connection failed')

# players = json.load(open(os.path.join(current_folder, 'players.json'), 'r'))

# for player in players:
#     values = f'''({player['wyId']}, "{player['shortName']}", "{player['firstName']}", "{player['middleName']}", "{player['lastName']}", "{player['height']}",\
# "{player['weight']}", "{player['birthDate']}","{player['birthArea']['id']}", "{player['passportArea']['id']}", 0,"{player['foot']}",\
# "{player['currentTeamId']}","{player['currentNationalTeamId']}","{player['gender']}","{player['status']}","{player['imageDataURL']}")'''
#     values = values.replace('""', 'null')
#     values = values.replace('"None"', 'null')
#     on_update = f'''shortName = "{player['shortName']}", firstName = "{player['firstName']}", middleName = "{player['middleName']}", lastName = "{player['lastName']}", height = "{player['height']}",\
# weight = "{player['weight']}", birthDate = "{player['birthDate']}",birthArea = "{player['birthArea']['id']}", passportArea = "{player['passportArea']['id']}",\
# foot = "{player['foot']}", currentTeamId = "{player['currentTeamId']}", currentNationalTeamId = "{player['currentNationalTeamId']}",\
# gender = "{player['gender']}", status = "{player['status']}", imageDataURL = "{player['imageDataURL']}"'''
#     on_update = on_update.replace('""', 'null')
#     on_update = on_update.replace('"None"', 'null')

#     db.insert_or_update('players', values,on_update)

# db.close_connection()