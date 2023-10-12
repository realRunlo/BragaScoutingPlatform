import json
import os
from MySQLdb import _mysql


class Db_handler:
    '''Class to handle mySql database connections'''

    db_config = None
    connection = None

    def __init__(self,config:dict=None,config_json:str=None) -> None:
        if config:
            self.db_config = config
        elif config_json:
            if os.path.exists(config_json):
                self.db_config = json.load(open(config_json, 'r'))



    def create_connection(self):
        """Creates a connection to the MySQL database"""
        try:
            self.connection = _mysql.connect(**self.db_config)
        except:
            self.connection = None


    def insert(self,table:str, values:str):
        """Inserts values into a table"""
        if self.connection:
            self.connection.query(f"""INSERT INTO scouting.{table} VALUES {values}""")
            self.connection.commit()

    def insert_or_update(self,table:str, values:str,on_update:str,parameters:str=''):
        """Inserts/updates values into a table"""
        if self.connection:
            #print(f'''INSERT INTO scouting.{table} {parameters} VALUES {values} ON DUPLICATE KEY UPDATE {on_update}''')
            self.connection.query(f'''INSERT INTO scouting.{table} {parameters} VALUES {values} ON DUPLICATE KEY UPDATE {on_update}''')
            self.connection.commit()


    def close_connection(self):
        """Closes the connection to the MySQL database"""
        if self.connection:
            self.connection.close()



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