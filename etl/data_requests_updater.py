'''Module that updates the requests files (for the db populating) and removes from db deprecated data'''



import argparse
import json
import os
from db import *
from api_handler import *


current_folder = os.path.dirname(os.path.abspath(__file__))
competitions_requests_folder = f'{current_folder}/competitions'


def parse_arguments():
    '''Define and parse arguments using argparse'''
    parser = argparse.ArgumentParser(description='wyscout API request')
    parser.add_argument('--db_config','-dbc'            ,type=str, nargs=1,required=True                                , help='Db config json file path')
    parser.add_argument('--update_request_files','-urf' ,action='store_true'                                              , help='Updates the requests files (for the db populating)')
    parser.add_argument('--remove_old_seasons','-ros'   ,action='store_true'                                            , help='Removes from db deprecated data, making a backup of it in the specified path')
    parser.add_argument('--fast_remove','-fr'           ,action='store_true'                                            , help='Removes from db deprecated data, disabling temporarily the foreign key checks (risky)')
    parser.add_argument('--log','-l'                    ,action='store_true'                                            , help="Activate logging, with optional log file path")
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
                                    comeptition_data['seasons'].append(season_data)
                        # add competition to new file data
                        new_file_data['competitions'].append(comeptition_data)
                    # save new file data
                    json.dump(new_file_data,open(f'{competitions_requests_folder}/{request_file}','w'),indent=4)

        else:
            print(f'No requests files found in {competitions_requests_folder}')
    else:
        print(f'No competitions folder found in {current_folder}')


def remove_old_seasons(db_handler:Db_handler,fast_remove=False):
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
    if seasons_to_remove:
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





def main(args,db_handler:Db_handler):
    '''Main function'''

    
    if args.update_request_files:
        print('Updating requests files')
        update_requests_files(db_handler)

    if args.remove_old_seasons:
        print('Removing old seasons from db')
        remove_old_seasons(db_handler,args.fast_remove)
        

        
    

if __name__ == "__main__":
    args = parse_arguments()
    if args.db_config[0].endswith('.json'):
        db_config_path = f'{current_folder}/{args.db_config[0]}'
        db_logger = None
        if args.log:
            logging.basicConfig(level=logging.INFO)
            db_logger = logging.getLogger('db_logger')

        # db request handler - for requests that are not time sensitive (can be done when available)
        db_request_handler = Db_handler(config_json=db_config_path,logger=db_logger)
        db_request_handler.create_connection()

        start_time = time.time()
        main(args,db_request_handler)
        end_time = time.time()
        print(f'Execution time: {end_time-start_time}')
        
    else:
        print("No db config file path specified")
        exit(1)
    


