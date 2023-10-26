import json
import os
import logging
import sys
import pymssql


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
            self.connection = pymssql.connect(**self.db_config)
            self.log('Connection to the database established')
        except Exception as e:
            self.connection = None
            self.log('Error creating connection to the database',logging.ERROR)
            self.log(e,logging.ERROR)


    def insert(self,table:str, values:str,database:str='scouting'):
        """Inserts values into a table"""
        if self.connection:
            self.log(f'''Query: INSERT INTO {database}.{table} VALUES {values}''')
            cursor = self.connection.cursor()
            try:
                cursor.execute(f"""INSERT INTO {database}.{table} VALUES {values}""")
                self.log(f'Values {values} inserted into table {table}')
            except Exception as e:
                self.log(f'Error inserting values {values} into table {table}\n{e}',logging.ERROR)
            cursor.close()

    def insert_or_update(self,table:str, values:str,key_parameters:list[str],parameters:str,update:bool=True,database:str='scouting'):
        """Inserts/updates values into a table"""
        if self.connection:
            #print(f'''INSERT INTO scouting.{table} {parameters} VALUES {values} ON DUPLICATE KEY UPDATE {on_update}''')
            self.log(f'''Query: INSERT INTO {database}.{table} {parameters} VALUES {values}''')
            cursor = self.connection.cursor()
            try:
                # create parameters group
                parameters_group = [f"[{param}]" for param in parameters]
                parameters_group = f"{','.join(parameters_group)}"
                # create on clause
                on_clause = []
                for key in key_parameters:
                    on_clause.append(f'target.[{key}] = source.[{key}]')
                on_clause = ' AND '.join(on_clause)
                
                # create insert values
                insert_values = []
                for param in parameters:
                    insert_values.append(f'source.[{param}]')
                insert_values = f"({','.join(insert_values)})"

                on_update = ''
                if update:
                    # create on update
                    on_update = []
                    for param in parameters:
                        if param not in key_parameters:
                            on_update.append(f'target.[{param}] = source.[{param}]')
                    on_update = ','.join(on_update)
                
                query = f'''MERGE {database}.{table} as target 
                                USING 
                                    (VALUES {values}) 
                                    AS source ({parameters_group})
                                ON ({on_clause})
                                WHEN NOT MATCHED THEN 
                                    INSERT ({parameters_group})
                                    VALUES {insert_values}'''
                if update and on_update != '':
                        query += f'''
                        WHEN MATCHED THEN 
                                        UPDATE SET {on_update}'''
                query += ';'
                cursor.execute(query)
                self.log(f'Values {values} inserted/updated into table {table}')
            except Exception as e:
                self.log(f'Error inserting/updating values {values} into table {table}\n{e}',logging.ERROR)
                open('error.txt','w', encoding="utf-8").write(query)
                sys.exit()
            self.connection.commit()
            cursor.close()


    
    def insert_or_update_many(self,table:str, values:list[str],key_parameters:list[str],parameters:str,update:bool=True,batch_size:int=500,database:str='scouting',delimiter:str=','):
        """Inserts/updates values into a table in batches using union all to connect values"""
        if self.connection:
            self.log(f'''Query: Inserting multiple values into {database}.{table}''')
            cursor = self.connection.cursor()
            try:
                batch = ' UNION ALL '.join(values[0:batch_size])
                # reduce batch_size if query is bigger than 0.7 MB
                while len(batch.encode('utf-8')) > 700000:
                    batch_size = int(batch_size/2)
                    batch = ' UNION ALL '.join(values[0:batch_size])
                i = 0

                # create parameters group
                parameters_group = [f"[{param}]" for param in parameters]
                parameters_group = f"{','.join(parameters_group)}"
                # create on clause
                on_clause = []
                for key in key_parameters:
                    on_clause.append(f'target.[{key}] = source.[{key}]')
                on_clause = ' AND '.join(on_clause)
                
                # create insert values
                insert_values = []
                for param in parameters:
                    insert_values.append(f'source.[{param}]')
                insert_values = f"({','.join(insert_values)})"

                on_update = ''
                if update:
                    # create on update
                    on_update = []
                    for param in parameters:
                        if param not in key_parameters:
                            on_update.append(f'target.[{param}] = source.[{param}]')
                    on_update = ','.join(on_update)

                # insert values
                while i < len(values):
                    batch = delimiter.join(values[i:i+batch_size])
                    if delimiter == ',':
                        batch = f'VALUES {batch}'
                    query = f'''MERGE {database}.{table} as target 
                                USING 
                                    ({batch}) 
                                    AS source ({parameters_group})
                                ON ({on_clause})
                                WHEN NOT MATCHED THEN 
                                    INSERT ({parameters_group}) 
                                    VALUES {insert_values}'''
                    if update and on_update != '':
                        query += f'''
                        WHEN MATCHED THEN 
                                        UPDATE SET {on_update}'''
                    query += ';'
                    cursor.execute(query)
                    i += batch_size
                self.log(f'Values inserted/updated into table {table}')
            except Exception as e:
                self.log(f'Error inserting/updating values into table {table}\n',logging.ERROR)
                self.log(e,logging.ERROR)
                open('error.txt','w', encoding="utf-8").write(query)
                sys.exit()
            self.connection.commit()
            cursor.close()


    def close_connection(self):
        """Closes the connection to the MySQL database"""
        if self.connection:
            self.connection.close()
            self.log('Connection to the database closed')

    def log(self, message:str,level=logging.INFO):
        """Logs a message"""
        if self.logger:
            self.logger.log(level,message)
