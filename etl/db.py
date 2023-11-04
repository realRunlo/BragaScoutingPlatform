import json
import os
import logging
import sys
import threading
import time
import pymssql


class Db_handler:
    '''Class to handle mySql database connections'''

    def __init__(self,config:dict=None,config_json:str=None,logger:logging.Logger=None) -> None:
        self.db_config = None
        self.connection = None
        self.logger = None
        self.request_queue = []
        self.request_queue_lock = threading.Lock()
        self.db_lock = threading.Lock()
        self.db_event = threading.Event()
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


    def run_request_handler(self,file_delimiter:str='|;|'):
        '''Run request_handler loop
        
        Handles requests to the database
        
        Allows for other work to be done while waiting for query to be executed'''
        if self.connection:
            while self.connection:
                if len(self.request_queue) > 0:
                    with self.request_queue_lock:
                        request = self.request_queue.pop(0)
                    values = ''
                    # get values from file
                    if 'values_file' in request:
                        if os.path.exists(request['values_file']):
                            values_file = open(request['values_file'],'r', encoding="utf-8")
                            values = values_file.read()
                            values_file.close()
                        
                    if request['type'] == 'insert' and values != '':
                        request['args']['values'] = values
                        self.insert(**request['args'])
                    elif request['type'] == 'update' and values != '':
                        request['args']['value'] = values
                        self.update(**request['args'])
                    elif request['type'] == 'insert_or_update' and values != '':
                        request['args']['values'] = values
                        self.insert_or_update(**request['args'])
                    elif request['type'] == 'insert_or_update_many' and values != '':
                        values = values.split(file_delimiter)
                        values = [value for value in values if value != '']
                        request['args']['values'] = values
                        self.insert_or_update_many(**request['args'])
                    # close connection and end loop
                    elif request['type'] == 'close_connection':
                        self.close_connection()

                    if 'values_file' in request:
                        os.remove(request['values_file'])
                else:
                    not_timeout = self.db_event.wait(timeout=1000)
                    self.db_event.clear()
                    if not not_timeout:
                        self.close_connection()
                        break
                



    def create_connection(self):
        """Creates a connection to the MySQL database"""
        with self.db_lock:
            try:
                self.connection = pymssql.connect(**self.db_config)
                self.log('Connection to the database established')
            except Exception as e:
                self.connection = None
                self.log('Error creating connection to the database',logging.ERROR)
                self.log(e,logging.ERROR)


    def close_connection(self):
        """Closes the connection to the MySQL database"""
        with self.db_lock:
            if self.connection:
                self.connection.close()
                self.connection = None
                self.db_event.set() # set event to wake up db_handler (in run method)
                self.log('Connection to the database closed')


    def request_close_connection(self):
        """Request to close the connection to the MySQL database"""
        if self.connection:
            with self.request_queue_lock:
                self.request_queue.append({'type':'close_connection'})
                self.db_event.set()

    def refresh_connection(self):
        """Refreshes the connection to the MySQL database"""
        with self.db_lock:
            print('Refreshing connection')
            self.close_connection()
            self.create_connection()
    


    def request_insert(self,table:str, values_file:str,database:str='scouting'):
        """Reuqest insert values into a table"""
        if self.connection:
            with self.request_queue_lock:
                self.request_queue.append({'type':'insert','args':{'table':table,'database':database},'values_file':values_file})
                self.db_event.set()

    def insert(self,table:str,values:str,database:str='scouting'):
        """Inserts values into a table"""
        if self.connection:
            self.log(f'''Query: INSERT INTO {database}.{table} VALUES {values}''')
            cursor = self.connection.cursor()
            try:
                cursor.execute(f"""INSERT INTO [{database}].[{table}] VALUES {values}""")
                self.log(f'Values {values} inserted into table {table}')
            except Exception as e:
                self.log(f'Error inserting values {values} into table {table}\n{e}',logging.ERROR)
            cursor.close()

    def request_update(self,table:str,parameter:str,values_file:str,where:str,database:str='scouting'):
        """Reuqest update values into a table"""
        if self.connection:
            with self.request_queue_lock:
                self.request_queue.append({'type':'update','args':{'table':table,'parameter':parameter,'where':where,'database':database},'values_file':values_file})
                self.db_event.set()

    def update(self,table:str,parameter:str,value:str,where:str,database:str='scouting',log:bool=False):
        """Update values into a table"""
        if self.connection:
            if log:
                self.log(f'''Query: UPDATE {database}.{table} SET {parameter} = {value} {where}''')
            cursor = self.connection.cursor()
            try:
                query = f'''UPDATE [{database}].[{table}] SET {parameter} = {value} {where}'''
                cursor.execute(query)
            except Exception as e:
                if log:
                    self.log(f'Error updating value {value} on {parameter} into table {table}\n{e}',logging.ERROR)
                open('error.txt','w', encoding="utf-8").write(query)
                sys.exit()
            self.connection.commit()
            cursor.close()

    def request_insert_or_update(self,table:str, values_file:str,key_parameters:list[str],parameters:str,update:bool=True,database:str='scouting'):
        """Reuqest insert/update values into a table"""
        if self.connection:
            with self.request_queue_lock:
                self.request_queue.append({'type':'insert_or_update','args':{'table':table,'key_parameters':key_parameters,'parameters':parameters,'update':update,'database':database},'values_file':values_file})
                self.db_event.set()

    def insert_or_update(self,table:str, values:str,key_parameters:list[str],parameters:str,update:bool=True,database:str='scouting'):
        """Inserts/updates values into a table"""
        if self.connection:
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
                
                query = f'''MERGE [{database}].[{table}] as target 
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

    def request_insert_or_update_many(self,table:str, values_file:str,key_parameters:list[str],parameters:str,update:bool=True,batch_size:int=500,database:str='scouting',delimiter:str=','):
        """Reuqest insert/update values into a table in batches using union all to connect values"""
        if self.connection:
            with self.request_queue_lock:
                self.request_queue.append({'type':'insert_or_update_many',
                                        'args':
                                        {
                                            'table':table,'key_parameters':key_parameters,'parameters':parameters,'update':update,'batch_size':batch_size,'database':database,'delimiter':delimiter
                                            }
                                            ,'values_file':values_file
                                        })
                self.db_event.set()

    
    def insert_or_update_many(self,table:str, values:list[str],key_parameters:list[str],parameters:str,update:bool=True,batch_size:int=500,database:str='scouting',delimiter:str=','):
        """Inserts/updates values into a table in batches using union all to connect values"""
        with self.db_lock:
            if self.connection:
                self.log(f'''Query: Inserting multiple values into {database}.{table}''')
                try:
                    cursor = self.connection.cursor()
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

                    errors = 0
                    # insert values
                    while i < len(values):
                        try:
                            batch = delimiter.join(values[i:i+batch_size])
                            if delimiter == ',':
                                batch = f'VALUES {batch}'
                            query = f'''MERGE [{database}].[{table}] as target 
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
                        except Exception as e:
                            self.log(f'Error inserting/updating values into table {table}\n',logging.ERROR)
                            self.log(e,logging.ERROR)
                            open('error.txt','w', encoding="utf-8").write(query)
                            # unknown error
                            if e.args[0] == 0 and errors < 10:
                                print('Error 0',e.args)
                                print(e)
                                cursor.close()
                                self.refresh_connection()
                                cursor = self.connection.cursor()
                                errors += 1
                                time.sleep(1)
                            else:
                                print('Error ',e.args[0],e.args)
                                print(e)
                                sys.exit()
                    self.log(f'Values inserted/updated into table {table}')
                    self.connection.commit()

                except Exception as e:
                    self.log(f'Error inserting/updating values into table {table}\n{e}',logging.ERROR)
                    open('error.txt','w', encoding="utf-8").write(query)
                    sys.exit()

                cursor.close()


    def select(self,table:str,parameters:str,where:str='',database:str='scouting',log:bool=False):
        """Selects values from a table"""
        with self.db_lock:
            if self.connection:
                if log:
                    self.log(f'''Query: SELECT {parameters} FROM [{database}].[{table}]''')
                tries = 0
                while tries < 10:
                    cursor = self.connection.cursor()
                    try:
                        cursor.execute(f'''SELECT {parameters} FROM [{database}].[{table}] {where}''')
                        if log:
                            self.log(f'Values selected from table {table}')
                        return cursor.fetchall()
                    except Exception as e:
                        if log:
                            self.log(f'Error selecting values from table {table}\n{e}',logging.ERROR)
                        cursor.close()
                        self.refresh_connection()
                        tries += 1
        return []

   

    def log(self, message:str,level=logging.INFO):
        """Logs a message"""
        if self.logger:
            self.logger.log(level,message)
