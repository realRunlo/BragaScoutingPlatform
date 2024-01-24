#!/usr/bin/python3.10

'''Module that updates the requests files (for the db populating) and removes from db deprecated data'''



import argparse
import json
import os
from db import *
from api_handler import *
import consts
from scouting_data import prepare_competitions_seasons_insert


current_folder = os.path.dirname(os.path.abspath(__file__))
competitions_requests_folder = f'{current_folder}/competitions'
tmp_folder  = f'{current_folder}/tmp'
file_delimiter = '|;|'

def parse_arguments():
    '''Define and parse arguments using argparse'''
    parser = argparse.ArgumentParser(description='wyscout API request')
    parser.add_argument('--db_config','-dbc'            ,type=str, nargs="?",const='config/db_cred.json',required=True                  , help='Db config json file path')
    parser.add_argument('--archive_db_config','-adbc'   ,type=str, nargs="?",const='config/archive_db_config.json'                      , help='Old db config json file path')
    parser.add_argument('--update_request_files','-urf' ,action='store_true'                                                            , help='Updates the requests files (for the db populating)\n Files are in the competitions folder inside the etl directory.')
    parser.add_argument('--remove_old_seasons','-ros'   ,action='store_true'                                                            , help='Removes from db deprecated data, making a backup of it in the specified path')
    parser.add_argument('--remove_season','-rs'         ,type=str, nargs='+'                                                            , help='Removes sepecfific seasons from db')
    parser.add_argument('--remove_competition','-rc'    ,type=str, nargs='+'                                                            , help='Removes sepecfific competitions from db')
    parser.add_argument('--fast_remove','-fr'           ,action='store_true'                                                            , help='Removes from db deprecated data, disabling temporarily the foreign key checks (risky)')
    parser.add_argument('--log','-l'                    ,action='store_true'                                                            , help='Activate logging, with optional log file path')
    return parser.parse_args()


def update_requests_files(db_handler:Db_handler):
    '''Update competitions requests files 

    * for each competition in file, check using api for the latest `3` seasons;
    * saves the corresponding seasons in the file;'''

    # get requests files
    if os.path.isdir(competitions_requests_folder):
        requests_files = os.listdir(competitions_requests_folder)
        if requests_files:
            # process each request file
            added_seasons = []
            for request_file in requests_files:
                print(f'Processing {request_file}')
                if request_file.endswith('.json'):
                    file_data = json.load(open(f'{competitions_requests_folder}/{request_file}','r'))
                    # get list of competitions
                    competitions = extract_competitions_info(file_data['competitions'])
                    new_file_data = file_data
                    new_file_data['competitions'] = []
                    # get seasons for each competition
                    for competition in competitions:
                        comeptition_data = competition
                        if competition['wyId']:
                            seasons = get_seasons_competitions(competition['wyId'])
                            if seasons:
                                comeptition_data['seasons'] = []
                                # order seasons by start date
                                seasons_sorted = sorted(seasons.items(),key=lambda x: datetime.datetime.strptime(x[1]['startDate'], '%Y-%m-%d'),reverse=True)
                                # remove seasons from the future
                                seasons_sorted = [season for season in seasons_sorted if datetime.datetime.strptime(season[1]['startDate'], '%Y-%m-%d') < datetime.datetime.now()]
                                # get most recent 3 seasons
                                seasons_sorted = seasons_sorted[:3]
                                # add seasons to competition data
                                for season in seasons_sorted:
                                    season_data = {
                                        'wyId':season[0],
                                        'name':season[1]['name'],
                                        'start':season[1]['startDate'],
                                        'end':season[1]['endDate']
                                    }
                                    added_seasons.append(season_data['wyId'])
                                    comeptition_data['seasons'].append(season_data)
                        # add competition to new file data
                        new_file_data['competitions'].append(comeptition_data)
                    # save new file data
                    json.dump(new_file_data,open(f'{competitions_requests_folder}/{request_file}','w'),indent=4)

            print(f'Inserting {len(added_seasons)} seasons into db')
            # get seasons data
            result_file = prepare_competitions_seasons_insert(added_seasons)
            values = open(f'{result_file}','r', encoding="utf-8").read().split(file_delimiter)
            values = [f'{value}' for value in values if value != '']
            # insert values
            db_handler.insert_or_update_many('competition_season',values,consts.competition_season_key_parameters,
                                             consts.competition_season_parameters,update=True)

            # remove last update log
            ## will force complete populating of these new seasons
            if os.path.exists(f'{current_folder}/last_update.txt'):
                os.remove(f'{current_folder}/last_update.txt')

        else:
            print(f'No requests files found in {competitions_requests_folder}')
    else:
        print(f'No competitions folder found in {current_folder}')


def insert_values(db_handler:Db_handler,table:str,values:list,batch_size:int=1000):
    '''Insert values in table
    
    * for each value, insert it in table;'''

    if values:
        for batch in range(0,len(values),batch_size):
            batch_values = values[batch:batch+batch_size]
            values_str = ''
            for value in batch_values:
                # remove generated columns
                if table == 'match':
                    value = value[:-2]
                values_str += '('
                for v in value:
                    if v  in ['NULL','null','None',None]:
                        values_str += 'NULL,'
                    else:
                        clean_value = str(v).replace('\'','\'\'')
                        values_str += f"'{clean_value}',"
                values_str = values_str[:-1]
                values_str += '),'
            values_str = values_str[:-1]
            db_handler.insert(table,values_str,ignore=True)


def migrate_data_to_archive_db(args:argparse.Namespace,db_handler:Db_handler,seasons_to_remove:list):
    '''Migrate data to archive database
    
    * for each season to remove, migrate data to archive database;'''

    if args.archive_db_config:
        print('Migrating data to archive database')

        archive_logger = None
        archive_db_config_path = f'{current_folder}/{args.archive_db_config}'
        if args.log:
            logging.basicConfig(level=logging.INFO)
            archive_logger = logging.getLogger('archive_logger')
        archive_db_handler = Db_handler(config_json=archive_db_config_path,logger=archive_logger)
        archive_db_handler.create_connection()

        # migrate areas (in case they are not in the archive db)
        areas = db_handler.select('area','*',log=True)
        insert_values(archive_db_handler,'area',areas)
        

        seasons_str = ','.join([str(s) for s in seasons_to_remove]) 


        ## get essential data 
        essential_tables = ['competition','competition_season','competition_season_round',
                            'competition_season_round_group','team','player','match']
        for table in essential_tables:
            print(f'Processing {table}')
            query = getattr(consts,table + '_data_query').format(replace=seasons_str)
            data = db_handler.execute(query,fetch=True,log=True)
            insert_values(archive_db_handler,table,data)
        ## get all other data
        tables = ['competition_season_scorer','competition_season_assistman',
            'team_competition_season','team_competition_season_round',
            'career_entry','player_positions','player_match_stats',
            'match_lineup','match_lineup_player_position','match_formation',
            'match_substitution','match_event_carry','match_event_pass',
            'match_event_shot','match_event_infraction','match_event_other',
            'match_goals']
        
        for table in tables:
            print(f'Processing {table}')
            query = getattr(consts,table + '_data_query').format(replace=seasons_str)
            data = db_handler.execute(query,fetch=True,log=True)
            insert_values(archive_db_handler,table,data,batch_size=2000)

        archive_db_handler.close_connection()
    else:
        print('No archive db config file path specified')

    



def remove_old_seasons(args:argparse.Namespace,db_handler:Db_handler,fast_remove=False):
    '''Remove from db deprecated data, making a backup of it
    
    * for each competition in db, leaves only the latest `3` seasons;'''

    # get competitions
    competitions = db_handler.select('competition','idcompetitions',log=True)
    print(f'Found {len(competitions)} competitions')
    query_remove_competition_season = open(f'{current_folder}/querys/delete_competition_season.sql','r',encoding='utf-8-sig').read()
    seasons_to_remove = []
    for competition in competitions:
        print(f'Processing competition {competition[0]}')
        # get seasons for competition
        seasons = db_handler.select('competition_season','"idcompetition_season","startDate"',where=f'where "competition"={competition[0]}',log=True)
        if seasons:
            # order seasons by start date
            seasons_sorted = sorted(seasons,key=lambda x: x[1],reverse=True)
            # leave only the latest 3 seasons
            seasons_sorted = seasons_sorted[:3]
            # get seasons to remove
            seasons_to_remove += [season[0] for season in seasons if season[0] not in [s[0] for s in seasons_sorted]]
    
    print(f'Removing {len(seasons_to_remove)} seasons')
    seasons_to_remove = [188653]
    print(seasons_to_remove)
    if seasons_to_remove:
        # migrate data to archive database
        migrate_data_to_archive_db(args,db_handler,seasons_to_remove)

        # get query to remove seasons
        query =  query_remove_competition_season.replace(r'(%replace%)','(' +','.join([str(s) for s in seasons_to_remove]) + ')')
        # disable foreign key checks, risky
        ## without this, the query will take a long time to execute (hours per season)
        if fast_remove:
            print('Fast remove - Disabling foreign key checks')
            query = f'''
            SET session_replication_role = 'replica';
            {query}
            SET session_replication_role = 'origin';
'''

        # remove seasons
        db_handler.execute(query,log=True)




def remove_seasons(args:argparse.Namespace,db_handler:Db_handler,seasons:list):
    '''Remove from db specified seasons'''

    # get query to remove seasons
    replace_str = ','.join([str(s) for s in seasons])
    query = open(f'{current_folder}/querys/delete_competition_season.sql','r',encoding='utf-8-sig').read()
    query = query.replace(r'%replace%',replace_str)

    # if fast remove, disable foreign key checks
    if args.fast_remove:
        print('Fast remove - Disabling foreign key checks')
        query = f'''
        SET session_replication_role = 'replica';
        {query}
        SET session_replication_role = 'origin';
'''
    
    # remove seasons
    db_handler.execute(query,log=True)

def remove_competitions(args:argparse.Namespace,db_handler:Db_handler):
    '''Remove from db specified competitions'''

    # get competitions
    competitions = args.remove_competition

    # get seasons
    competitions = ','.join([str(c) for c in competitions])
    seasons = db_handler.select('competition_season','"idcompetition_season"',where=f'where "competition" IN ({competitions})',log=True)
    seasons = [season[0] for season in seasons]
    if seasons:
        # remove seasons
        print(f'Removing {len(seasons)} seasons')
        remove_seasons(args,db_handler,seasons)

    # remove competitions
    print(f'Removing competitions')
    db_handler.execute(f'DELETE FROM scouting.competition WHERE idcompetitions IN ({competitions})',log=True)




def main(args,db_handler:Db_handler):
    '''Main function'''

    
    if args.update_request_files:
        print('Updating requests files')
        update_requests_files(db_handler)

    if args.remove_old_seasons:
        print('Removing old seasons from db')
        remove_old_seasons(args,db_handler,args.fast_remove)

    if args.remove_season:
        print(f'Removing seasons {args.remove_season}')
        remove_seasons(args,db_handler,args.remove_season)

    if args.remove_competition:
        print(f'Removing competition {args.remove_competition}')
        remove_competitions(args,db_handler)
        

        
    

if __name__ == "__main__":
    args = parse_arguments()
    if args.db_config.endswith('.json'):
        db_config_path = f'{current_folder}/{args.db_config}'
        db_logger = None
        if args.log:
            logging.basicConfig(level=logging.INFO)
            db_logger = logging.getLogger('db_logger')

        # data insert tmp folder
        if not os.path.exists(tmp_folder):
            os.mkdir(tmp_folder)
        # clean folder
        else:
            for file in os.listdir(tmp_folder):
                os.remove(f'{tmp_folder}/{file}')

        print('Connecting to db')
        db_request_handler = Db_handler(config_json=db_config_path,logger=db_logger)
        db_request_handler.create_connection()

        start_time = time.time()
        main(args,db_request_handler)
        end_time = time.time()
        print(f'Execution time: {end_time-start_time}')
        
    else:
        print("No db config file path specified")
        exit(1)
    


