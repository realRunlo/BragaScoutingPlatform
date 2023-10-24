import json
import os
import argparse
import time
import logging
from db import Db_handler
from multiprocessing.pool import ThreadPool
from utils import get_similar
from api_handler import *




def parse_arguments():
    '''Define and parse arguments using argparse'''
    parser = argparse.ArgumentParser(description='wyscout API request')
    parser.add_argument('--db_config','-dbc'            ,type=str, nargs=1,required=True                                , help='Db config json file path')
    parser.add_argument('--areas','-a'                  ,action='store_true'                                            , help='Request areas from API')
    parser.add_argument('--area_competitions','-ac'     ,type=str, nargs='+'                                            , help="Request area's competitions from API")
    parser.add_argument('--competition_info','-ci'      ,type=str, nargs='*'                                            , help="Request all info from competition from API")
    parser.add_argument('--competition_players','-cp'   ,type=str, nargs='+'                                            , help="Request competition's players from API")
    parser.add_argument('--full_info','-fi'             ,type=str, nargs=1                                              , help="Request all info from API, according to json file provided")
    parser.add_argument('--log','-l'                    ,action='store_true'                                            , help="Activate logging, with optional log file path")
    return parser.parse_args()



def run_threaded_for(func,iterable, args=None,log=False,threads:int=6):
    '''Runs a function for each value in iterable'''
    if log:
        start_time = time.time()
        print(f'Threaded: Running {func.__name__} to gather info from {len(iterable)} items ')
    iterable_divided = [None]*threads
    max_slice_size = len(iterable)//threads
    # divide work between threads
    for i in range(threads):
        if i == threads-1:
            iterable_divided[i] = iterable[i*max_slice_size:]
        else:
            iterable_divided[i] = iterable[i*max_slice_size:(i+1)*max_slice_size]
            
    thread_args = [[x,args] if args else [x] for x in iterable_divided]
    pool = ThreadPool(threads)
    results = pool.starmap(func,thread_args)
    pool.close()
    pool.join()
    if log:
        print(f'Threaded: Finished {func.__name__} in {time.time()-start_time} seconds')
    return results

    


def extract_competitions_info(competitions:list):
    '''Extracts competitions metadata (id, seasons) from json config file'''
    competitions_info = []
    area_competitions = []
    competitions_names = []
    last_area_code = None
    for competition in competitions:
        c_i = {
            'wyId':None,
            'seasons':[]
        }
        if 'wyId' in competition:
            c_i['wyId'] = competition['wyId']
        else:
            if 'area' in competition and 'name' in competition:
                areaCode = competition['area']
                competition_name = competition['name']
                if areaCode != last_area_code: #Como ele recebe uma lista de competiçoes no ficheiro, se estas forem todas da mesma área é escusado estar sempre a ir buscar a informaçao a api para encontrar o id delas
                    area_competitions = get_area_competitions(area=areaCode)
                    competitions_names = [c['name'] for c in area_competitions]
                else:
                    last_area_code = areaCode
                true_competition_name = get_similar(competitions_names,competition_name)
                c_i['wyId'] = [c['wyId'] for c in area_competitions if c['name'] == true_competition_name][0]
            else:
                #ERROR
                continue
        for season in competition['seasons']:
            if 'wyId' in season:
                c_i['seasons'].append(season['wyId'])
            elif 'start' in season and 'end' in season:
                start = season['start']
                end = season['end']
                seasons_list = get_seasons_competitions(c_i['wyId'])
                seasonsId = [k for k,v in seasons_list.items() if v['startDate'][0:4] == start and v['endDate'][0:4] == end] #Neste momento so estamos a comparar os anos, se calhar deviamos ver isto melhor
                for seasonId in seasonsId:
                    c_i['seasons'].append(seasonId)
            else:
                #Error
                continue
        competitions_info.append(c_i)
    return competitions_info

def prepare_areas_insert(areas):
    '''Inserts area into db'''
    querys = []
    for area in areas:
        values = f'''({area['id']}, "{area['name']}", "{area['alpha3code']}")'''
        querys.append(values)
    return querys

def populate_areas(db_handler:Db_handler):
    '''Populates areas table in db'''
    areas = get_areas()
    query_values = prepare_areas_insert(areas)
    on_update = f'''name=new.name, alpha3code=new.alpha3code'''
    parameters = f'''(idareas, name, alpha3code)'''
    db_handler.insert_or_update_many('area',query_values,on_update=on_update,parameters=parameters)




def populate_competitions(db_handler:Db_handler,competitions_id:list):
    '''Populates competitions table in db'''
    c_i = 0
    for competition_id in competitions_id:
        print(f'Requesting competition {c_i}/{len(competitions_id)}')
        competition_info = get_competition_info(competition_id)
        if competition_info:
            values = f'''({competition_info['wyId']}, "{competition_info['name']}", "{competition_info['area']['id']}", "{competition_info['gender']}",\
                         "{competition_info['type']}", "{competition_info['format']}", "{competition_info['divisionLevel']}", "{competition_info['category']}")'''
            
            on_update = f'''name="{competition_info['name']}", area="{competition_info['area']['id']}", gender="{competition_info['gender']}",\
                            type="{competition_info['type']}", format="{competition_info['format']}", divisionLevel="{competition_info['divisionLevel']}", category="{competition_info['category']}"'''

            db_handler.insert_or_update('competition',values,on_update)
        c_i += 1


def populate_competitions_seasons(db_handler:Db_handler,seasons_id:list):
    '''Populates seasons table in db'''
    s_i = 0
    for season_id in seasons_id:
        print(f'Requesting season {s_i}/{len(seasons_id)}')
        season_info = get_season_info(season_id)
        if season_info:
            values = f'''({season_info['wyId']}, "{season_info['startDate']}", "{season_info['endDate']}", "{season_info['name']}", "{season_info['competitionId']}")'''
            on_update = f'''startDate="{season_info['startDate']}", endDate="{season_info['endDate']}", name="{season_info['name']}", competition="{season_info['competitionId']}"'''
            parameters = f'''(idcompetition_season, startDate, endDate, name, competition)'''
            db_handler.insert_or_update('competition_season',values,on_update,parameters)
        s_i += 1


def prepare_teams_insert(teams,season_id:int):
    '''Inserts team into db, as well as team_competition_season table'''

    querys = []
    for team in teams:
        team_info = team['team']
        if team_info:
            values = f'''({team_info['wyId']}, "{team_info['name']}", "{team_info['officialName']}", "{team_info['imageDataURL']}", "{team_info['gender']}", "{team_info['type']}",\
                        "{team_info['city']}", "{team_info['category']}", "{team_info['area']['id']}")'''
            querys.append(('team',values))

            values = f'''("{season_id}", "{team_info['wyId']}","{team['totalDraws']}","{team['totalGoalsAgainst']}","{team['totalGoalsFor']}","{team['totalLosses']}",\
                        "{team['totalPlayed']}","{team['totalPoints']}","{team['totalWins']}")'''
            querys.append(('team_competition_season',values))
    return querys

    

def populate_teams(db_handler:Db_handler,season_id:int):
    '''Populates teams table in db, as well as team_competition_season table'''
    season_info = get_season_info(season_id)
    if season_info:
        teams = get_season_standings(season_id)
        result = run_threaded_for(prepare_teams_insert,teams,log=True,args=(season_id))
        querys = [query for query_list in result for query in query_list]
        team_query_values = []
        team_competition_season_query_values = []
        # separate querys
        for query in querys:
            if query[0] == 'team':
                team_query_values.append(query[1])
            elif query[0] == 'team_competition_season':
                team_competition_season_query_values.append(query[1])

        team_on_update = f'''name=new.name, official_name=new.official_name, icon=new.icon, gender=new.gender, type=new.type,\
                             city=new.city, category=new.category, area=new.area'''
        team_parameters = f'''(idteam,name,official_name,icon,gender,type,city,category,area)'''
        
        team_competition_season_on_update = f'''competition_season=new.competition_season, team=new.team, totalDraws=new.totalDraws, totalGoalsAgainst=new.totalGoalsAgainst,\
                                                totalGoalsFor=new.totalGoalsFor, totalLosses=new.totalLosses, totalPlayed=new.totalPlayed, totalPoints=new.totalPoints, totalWins=new.totalWins'''
        team_competition_season_parameters = f'''(competition_season, team, totalDraws, totalGoalsAgainst, totalGoalsFor, totalLosses, totalPlayed, totalPoints, totalWins)'''
        db_handler.insert_or_update_many('team',team_query_values,on_update=team_on_update,parameters=team_parameters)
        db_handler.insert_or_update_many('team_competition_season',team_competition_season_query_values,on_update=team_competition_season_on_update,parameters=team_competition_season_parameters)
        

def prepare_players_insert(players,player_advanced_stats:bool=False):
    querys = []
    for player in players:
        contractInfo = get_player_contract_info(player['wyId'])
        contractExpiration = contractInfo['contractExpiration']
        player_agencies = ""
        if 'agencies' in contractInfo and len(contractInfo['agencies']) > 0:
            player_agencies = contractInfo['agencies'][0]
            for agencie in contractInfo['agencies'][1:]:
                player_agencies+= ', ' + agencie

        player_name = player['firstName'] + ' ' + player['middleName'] + ' ' + player['lastName']
        values = f'''({player['wyId']}, "{player_name}", "{player['shortName']}", "{player['birthArea']['id']}", "{player['birthDate']}", "{player['imageDataURL']}", "{player['foot']}",\
                    "{player['height']}","{player['weight']}","{player['status']}","{player['gender']}","{player['role']['code2']}", "{player['role']['code3']}", "{player['role']['name']}"
                    ,"{contractExpiration}","{player_agencies}")'''
        querys.append(('player',values))

        # get player advanced stats
        if player_advanced_stats:
            career = get_player_career(player['wyId'])
            career = get_latest_career_entries(career,entries=5)
            for entry in career:
                season = entry['seasonId']
                team = entry['teamId']
                competition = entry['competitionId']
                # populate career table
                values = f'''SELECT '{player['wyId']}', idteam_competition_season, '{entry['appearances']}','{entry['goal']}','{entry['minutesPlayed']}',\
                            '{entry['penalties']}','{entry['redCards']}','{entry['shirtNumber']}','{entry['substituteIn']}','{entry['substituteOnBench']}',\
                            '{entry['substituteOut']}','{entry['yellowCard']}' FROM scouting.team_competition_season WHERE team={team} AND competition_season={season}'''
                querys.append(('career_entry',values))

                advanced_stats = get_player_advanced_stats(player['wyId'],competition,season)
                if advanced_stats:
                    # populate positions table
                    positions = advanced_stats['positions']
                    for position in positions:
                        values = f'''SELECT '{player['wyId']}', '{position['percent']}','{position['position']['code']}', '{position['position']['name']}',idteam_competition_season \
                                    FROM scouting.team_competition_season WHERE team='{team}' AND competition_season='{season}' '''
                        querys.append(('player_positions',values))
    return querys
        
    

def populate_players(db_handler:Db_handler,season_id:int,player_advanced_stats:bool=False):
    '''Populates players table in db'''
    print(f'Populating players from season {season_id}')
    players = get_season_players(season_id)
    result = run_threaded_for(prepare_players_insert,players,log=True,args=(player_advanced_stats),threads=12)
    querys = [query for query_list in result for query in query_list]
    player_querys_values = []
    player_positions_querys_values = []
    career_entry_querys_values = []
    # separate querys
    for query in querys:
        if query[0] == 'player':
            player_querys_values.append(query[1])
        elif query[0] == 'player_positions':
            player_positions_querys_values.append(query[1])
        elif query[0] == 'career_entry':
            career_entry_querys_values.append(query[1])

    playere_on_update = f'''name=new.name, short_name=new.short_name, birth_area=new.birth_area, birth_date=new.birth_date, image=new.image, foot=new.foot,\
                            height=new.height, weight=new.weight, status=new.status, gender=new.gender, role_code2=new.role_code2, role_code3=new.role_code3, role_name=new.role_name,contract_expiration=new.contract_expiration, contract_agency=new.contract_agency'''
    player_parameters = f'''(idplayer,name,short_name,birth_area,birth_date,image,foot,height,weight,status,gender,role_code2,role_code3,role_name,contract_expiration,contract_agency)'''
    db_handler.insert_or_update_many('player',player_querys_values,on_update=playere_on_update,parameters=player_parameters)

    career_entry_on_update = f'''player=VALUES(player), team_competition_season=VALUES(team_competition_season), appearances=VALUES(appearances), goal=VALUES(goal), minutesPlayed=VALUES(minutesPlayed),\
                                penalties=VALUES(penalties), redCards=VALUES(redCards), shirtNumber=VALUES(shirtNumber), substituteIn=VALUES(substituteIn), substituteOnBench=VALUES(substituteOnBench),\
                                substituteOut=VALUES(substituteOut), yellowCard=VALUES(yellowCard)'''
    career_parameters = f'''(player, team_competition_season, appearances, goal, minutesPlayed, penalties, redCards, shirtNumber, substituteIn, substituteOnBench, substituteOut, yellowCard)'''
    db_handler.insert_or_update_many_union('career_entry',career_entry_querys_values,on_update=career_entry_on_update,parameters=career_parameters)
    
    if player_advanced_stats:
        player_positions_on_update = f'''percent=VALUES(percent), name=VALUES(name)'''
        player_positions_parameters = f'''(player, percent, code, name,team_competition_season)'''
        db_handler.insert_or_update_many_union('player_positions',player_positions_querys_values,on_update=player_positions_on_update,parameters=player_positions_parameters)


def prepare_match_players_stats_insert(match:int):
    '''Prepare values for player_match_stats table in db'''
    querys = []
    match_players_stats = get_match_players_stats(match)
    for player_stats in match_players_stats:
        player = player_stats['playerId']
        offensive_duels = player_stats['total']['offensiveDuels']
        progressive_passes = player_stats['total']['progressivePasses']
        forward_passes = player_stats['total']['forwardPasses']
        crosses = player_stats['total']['crosses']
        key_passes = player_stats['total']['keyPasses']
        defensive_duels = player_stats['total']['defensiveDuels']
        interceptions = player_stats['total']['interceptions']
        recoveries = player_stats['total']['recoveries']
        successful_passes = player_stats['percent']['successfulPasses']
        long_passes = player_stats['total']['longPasses']
        aerial_duels = player_stats['total']['aerialDuels']
        losses = player_stats['total']['losses']
        own_half_losses = player_stats['total']['ownHalfLosses']
        goal_kicks = player_stats['total']['goalKicks']
        received_pass = player_stats['total']['receivedPass']
        dribbles = player_stats['total']['dribbles']
        touch_in_box = player_stats['total']['touchInBox']
        opponent_half_recoveries = player_stats['total']['opponentHalfRecoveries']

        values = f'''("{match}", "{player}", "{offensive_duels}", "{progressive_passes}", "{forward_passes}", "{crosses}", "{key_passes}", "{defensive_duels}", "{interceptions}", "{recoveries}",\
        "{successful_passes}", "{long_passes}", "{aerial_duels}", "{losses}", "{own_half_losses}", "{goal_kicks}", "{received_pass}", "{dribbles}", "{touch_in_box}", "{opponent_half_recoveries}")'''

        querys.append(('player_match_stats',values))
    return querys


def prepare_match_formation_insert(match:int,match_team_info:dict):
    '''Prepare values for match_formation table in db'''
    querys = []
    for team,team_info in match_team_info.items():
        formation = team_info['formation']
        substitutes = {}
        # get team substitutions
        for player in formation['substitutions']:
            substitutes[player['playerIn']] = {}
            substitutes[player['playerIn']]['playerIn'] = player['playerIn']
            substitutes[player['playerIn']]['playerOut'] = player['playerOut']
            substitutes[player['playerIn']]['minute'] = player['minute']
            values = f'''("{match}", "{substitutes[player['playerIn']]['playerIn']}", "{substitutes[player['playerIn']]['playerOut']}", "{team}", "{substitutes[player['playerIn']]['minute']}")'''
            querys.append(('match_substitution',values))
        # team initial lineup
        for player in formation['lineup']:
            player_id = player['playerId']
            assists = player['assists']
            goals = player['goals']
            own_goals = player['ownGoals']
            red_cards = player['redCards']
            shirt_number = player['shirtNumber']
            yellow_cards = player['yellowCards']
            minute = 0
            type = 'lineup'
            values = f'''("{match}", "{player_id}", "{assists}", "{goals}", "{own_goals}", "{red_cards}", "{shirt_number}", "{yellow_cards}", "{minute}", "{team}", "{type}")'''
            querys.append(('match_formation',values))
        # team bench
        for player in formation['bench']:
            player_id = player['playerId']
            assists = player['assists']
            goals = player['goals']
            own_goals = player['ownGoals']
            red_cards = player['redCards']
            shirt_number = player['shirtNumber']
            yellow_cards = player['yellowCards']
            minute = 0
            type = 'bench'
            if player['playerId'] in substitutes:
                minute = substitutes[player['playerId']]['minute']
                type = 'substitution'
            values = f'''("{match}", "{player_id}", "{assists}", "{goals}", "{own_goals}", "{red_cards}", "{shirt_number}", "{yellow_cards}", "{minute}", "{team}", "{type}")'''
            querys.append(('match_formation',values))
    return querys




def prepare_matches_insert(matches,player_advanced_stats:bool=False):
    querys = []
    for match in matches:
        match_info = get_match_info(match['matchId'])
        # get match basic info
        if match_info:
            home_team = match_info['teamsData']['home']['teamId']
            home_score = match_info['teamsData']['home']['score']
            away_team = match_info['teamsData']['away']['teamId']
            away_score = match_info['teamsData']['away']['score']
            winner = match_info['winner']
            values = f'''({match_info['wyId']},"{match_info['seasonId']}", "{home_team}", "{away_team}", "{match_info['dateutc']}",\
            "{home_score}","{away_score}", "{winner}")'''

            querys.append(('match',values))

            match_events = get_match_events(match['matchId'])
            match_lineups = get_match_lineups(match['matchId'])

            # get team's match formation
            querys += prepare_match_formation_insert(match['matchId'],match_info['teamsData'])
            
            # get match lineups
            if match_lineups:
                teams = [x for x in match_lineups if x != "teams"]
                for team in teams:
                    lineup_info = match_lineups[team]
                    for part,times in lineup_info.items():
                        for time,lineups in times.items():
                            for lineup in lineups:
                                values = f'''("{match['matchId']}", "{team}", "{part}", "{time}",{lineups[lineup]['scheme']})'''
                                querys.append(('match_lineup',values))
                                players = lineups[lineup]['players']
                                # players positions in lineup
                                for playerdict in players:
                                    for playerId in playerdict:
                                        position = playerdict[playerId]['position']
                                        values = f'''SELECT match_lineup_id, {playerId},{position} FROM scouting.match_lineup WHERE match={match['matchId']} AND team={team} AND period={part} AND second={time}'''
                                        querys.append(('match_lineup_player_position',values))

            # get match advanced stats for each player
            if player_advanced_stats:
                query_list = prepare_match_players_stats_insert(match['matchId'])
                querys += query_list

            # get match events
            for event in match_events:
                id = event['id']
                matchid = event['matchId']
                player = event['player']['id']
                matchTimestamp = event['matchTimestamp']
                matchPeriod = event['matchPeriod']
                if event['location'] != None:
                    location_x = event['location']['x']
                    location_y = event['location']['y']
                else:
                    location_x = -1 #TODO: ver melhor isto
                    location_y = -1 #TODO: ver melhor isto
                minute = event['minute']
                second = event['second']
                team = event['team']['id']
                opponentTeam = event['opponentTeam']['id']
                type = event['type']['primary']
                details = {}
                if event['pass'] != None:
                    details['pass'] = event['pass']
                if event['shot'] != None:
                    details['shot'] = event['shot']
                if event['groundDuel'] != None:
                    details['groundDuel'] = event['groundDuel']
                if event['aerialDuel'] != None:
                    details['aerialDuel'] = event['aerialDuel']
                if event['infraction'] != None:
                    details['infraction'] = event['infraction']
                if event['carry'] != None:    
                    details['carry'] = event['carry']
                if event['possession'] != None:   
                    details['possession'] = event['possession']
                relatedEventId = event['relatedEventId']
                
                values = f'''("{id}", "{matchid}", "{player}", "{matchTimestamp}", "{matchPeriod}", "{location_x}", "{location_y}", "{minute}", "{second}", 
                "{team}", "{opponentTeam}", "{type}", "{details}", "{relatedEventId}")'''
                
                querys.append(('match_event',values))

                secondary_types = event['type']['secondary']
                for secondary_type in secondary_types:
                    valuesst = f'''("{id}","{secondary_type}")'''
                    querys.append(('match_event_secondary_type',valuesst))

    return querys
        



def populate_matches(db_handler:Db_handler,season_id:int,player_advanced_stats:bool=False):
    '''Populates matches table in db, gathering matches from given season\n
    Can gather advanced stats from players in each match'''
    print(f'Populating matches from season {season_id}')
    matches = get_season_matches(season_id)
    result = run_threaded_for(prepare_matches_insert,matches,log=True,args=(player_advanced_stats),threads=10)
    querys = [query for query_list in result for query in query_list]
    match_query_values = []
    player_match_stats_query_values = []
    match_lineup_values = []
    match_lineup_player_position_values = []
    match_formation_values = []
    match_substitution_values = []
    match_events_values = []
    events_secondary_types_values = []
    # separate querys
    for query in querys:
        if query[0] == 'match':
            match_query_values.append(query[1])
        elif query[0] == 'player_match_stats':
            player_match_stats_query_values.append(query[1])
        elif query[0] == 'match_lineup':
            match_lineup_values.append(query[1])
        elif query[0] == 'match_lineup_player_position':
            match_lineup_player_position_values.append(query[1])
        elif query[0] == 'match_formation':
            match_formation_values.append(query[1])
        elif query[0] == 'match_substitution':
            match_substitution_values.append(query[1])
        elif query[0] == 'match_event':
            match_events_values.append(query[1])
        elif query[0] == 'match_event_secondary_type':
            events_secondary_types_values.append(query[1])

    # match table
    match_on_update = f'''competition_season=new.competition_season, home_team=new.home_team, away_team=new.away_team, date=new.date,\
                          home_score=new.home_score, away_score=new.away_score, winner=new.winner'''
    match_parameters = f'''(idmatch, competition_season, home_team, away_team, date, home_score, away_score, winner)'''
    db_handler.insert_or_update_many('match',match_query_values,on_update=match_on_update,parameters=match_parameters)

    if player_advanced_stats:
        # player_match_stats table
        player_match_stats_on_update = f'''`match`=new.match, player=new.player, offensiveDuels=new.offensiveDuels,\
                                            progressivePasses=new.progressivePasses, forwardPasses=new.forwardPasses,crosses=new.crosses, keyPasses=new.keyPasses,\
                                            defensiveDuels=new.defensiveDuels, interceptions=new.interceptions, recoveries=new.recoveries,\
                                            successfulPasses=new.successfulPasses, longPasses=new.longPasses, aerialDuels=new.aerialDuels, \
                                            losses=new.losses, ownHalfLosses=new.ownHalfLosses, goalKicks=new.goalKicks, receivedPass=new.receivedPass, dribbles=new.dribbles, touchInBox=new.touchInBox'''
        player_match_stats_parameters = f'''(`match`, player, offensiveDuels, progressivePasses, forwardPasses, crosses, keyPasses, defensiveDuels, interceptions, recoveries,\
        successfulPasses, longPasses, aerialDuels, losses, ownHalfLosses, goalKicks, receivedPass, dribbles, touchInBox, opponentHalfRecoveries)'''
        db_handler.insert_or_update_many('player_match_stats',player_match_stats_query_values,on_update=player_match_stats_on_update,parameters=player_match_stats_parameters)

    # match_lineup table
    match_lineup_on_update = f'''`match`=new.match, team=new.team, period=new.period, second=new.second, lineup=new.lineup'''
    match_lineup_parameters = f'''(`match`, team, period, second, lineup)'''
    db_handler.insert_or_update_many('match_lineup',match_lineup_values,on_update=match_lineup_on_update,parameters=match_lineup_parameters)

    # match_lineup_player_position table
    match_lineup_player_position_parameters = f'''(match_lineup_id, player, position)'''
    db_handler.insert_or_update_many_union('match_lineup_player_position',match_lineup_player_position_values,parameters=match_lineup_player_position_parameters)

    # match_formation table
    match_formation_on_update = f'''`match`=new.match, player=new.player, assists=new.assists, goals=new.goals, own_goals=new.own_goals, red_cards=new.red_cards, shirt_number=new.shirt_number,\
                                    yellow_cards=new.yellow_cards, minute=new.minute, team=new.team, type=new.type'''
    match_formation_parameters = f'''(idmatch_formation, `match`, player, assists, goals, own_goals, red_cards, shirt_number, yellow_cards, minute, team, type)'''
    db_handler.insert_or_update_many('match_formation',match_formation_values,on_update=match_formation_on_update,parameters=match_formation_parameters)

    # match_substitution table
    match_substitution_on_update = f'''`match`=new.match, playerIn=new.playerIn, playerOut=new.playerOut, team=new.team, minute=new.minute'''
    match_substitution_parameters = f'''(`match`, playerIn, playerOut, team, minute)'''
    db_handler.insert_or_update_many('match_substitution',match_substitution_values,on_update=match_substitution_on_update,parameters=match_substitution_parameters)

    # match_event table
    event_on_update = f'''`match`=new.match, player=new.player, matchTimestamp=new.matchTimestamp, matchPeriod=new.matchPeriod, location_x=new.location_x, location_y=new.location_y,\
                        minute=new.minute, second=new.second, team=new.team, opponentTeam=new.opponentTeam, type=new.type, details=new.details, relatedEventId=new.relatedEventId'''
    event_parameters = f'''(idmatch_event, match, player, matchTimestamp, matchPeriod, location_x, location_y, minute, second, team, opponentTeam, type, details, relatedEventId)'''
    db_handler.insert_or_update_many('match_event', match_events_values, on_update=event_on_update, parameters=event_parameters)

    # match_event_secondary_type table
    secondary_type_parameters = f'''(match_event, secondary_type)'''
    db_handler.insert_or_update_many('match_event_secondary_type', events_secondary_types_values, parameters=secondary_type_parameters)
    


def populate_rounds(db_handler:Db_handler,season_id:int):
    '''Populates rounds table in db'''
    print(f'Populating rounds from season {season_id}')
    season_rounds = get_season_career(season_id)
    querys = []
    for round in season_rounds:
        values = f'''("{season_id}","{round['startDate']}", "{round['endDate']}", "{round['name']}" )'''
        querys.append(values)
    on_update = f'''name=new.name'''
    parameters = f'''(competition_season, startDate, endDate, name)'''
    db_handler.insert_or_update_many('round',querys,on_update=on_update,parameters=parameters)

        


def main(args,db_handler:Db_handler):
    '''Main function'''

    #TODO : treat other optional flags

    # get full info
    if args.full_info:
        request_file_path = f'{current_folder}/{args.full_info[0]}'
        if request_file_path.endswith('json') and os.path.exists(request_file_path):
            request_file = json.load(open(request_file_path))
            # populate areas
            #populate_areas(db_handler) 
            if 'competitions' in request_file:
                competitions = request_file['competitions']
                competitions_info = extract_competitions_info(competitions)
                #print(competitions_info)
                competitions_id = [c['wyId'] for c in competitions_info]
                # populate competitions
                #populate_competitions(db_handler,competitions_id)

                # populate seasons
                seasons_id = [s for c in competitions_info for s in c['seasons']]
                #populate_competitions_seasons(db_handler,seasons_id)

                s_i = 1
                # populate teams, players, matches and stats
                for s_id in seasons_id:
                    print(f'Extracting info from season {s_i}/{len(seasons_id)}')
                    #populate_teams(db_handler,s_id)
                    #populate_players(db_handler,s_id,player_advanced_stats=True)
                    populate_matches(db_handler,s_id,player_advanced_stats=True)
                    populate_rounds(db_handler,s_id)
                    s_i += 1

        else:
            print('Invalid request file. Please provide a valid .json file.')




if __name__ == '__main__':
    args = parse_arguments()

    if args.db_config[0].endswith('.json'):
        db_config_path = f'{current_folder}/{args.db_config[0]}'
        db_logger = None
        main_logger = None
        if args.log:
            logging.basicConfig(level=logging.INFO)
            db_logger = logging.getLogger('db_logger')
            main_logger = logging.getLogger('main_logger')
            main_logger.log(logging.INFO,'Logging active')
        db_handler = Db_handler(config_json=db_config_path,logger=db_logger)
        db_handler.create_connection()
        if db_handler.connection:
            main(args,db_handler)
            db_handler.close_connection()
        else:
            print('DB connection failed to be established.')
    else:
        print('Invalid db config file. Please provide a .json file.')



                        