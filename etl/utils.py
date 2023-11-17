import datetime
import jellyfish
from api_handler import *

def get_similar(list : [str],word : str):
    return max([(jellyfish.jaro_similarity(word, w),w) for w in list])[1]


def similarity(word : str, right_word : str):
    return jellyfish.jaro_similarity(right_word, word)



def working_hours():
    '''Returns True if current time is between 8h and 19h'''
    now = datetime.datetime.now()
    return now.hour >= 8 and now.hour < 19


def extract_competitions_info(competitions:list):
    '''Extracts competitions metadata (id, seasons) from json config file'''
    competitions_info = {}
    competition_list = []
    area_competitions = []
    competitions_names = []
    last_area_code = None
    for competition in competitions:
        c_i = {
            'wyId':None,
            "name": None,
            "area": None,
            'custom_name' : None,
            'tm_code':None,
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
        if 'tm_code' in competition:
            c_i['custom_name'] = competition['tm_code']
            c_i['tm_code'] = competition['tm_code']
        if 'name' in competition:
            c_i['name'] = competition['name']
        if 'area' in competition:
            c_i['area'] = competition['area']
        for season in competition['seasons']:
            if 'wyId' in season and season['wyId'] not in c_i['seasons']:
                c_i['seasons'].append(season['wyId'])
            elif 'start' in season and 'end' in season:
                start = season['start']
                end = season['end']
                seasons_list = get_seasons_competitions(c_i['wyId'])
                seasonsId = [k for k,v in seasons_list.items() if v['startDate'][0:4] == start and v['endDate'][0:4] == end] #Neste momento so estamos a comparar os anos, se calhar deviamos ver isto melhor
                for seasonId in seasonsId:
                    if seasonId not in c_i['seasons']:
                        c_i['seasons'].append(seasonId)
            else:
                #Error
                continue
        competitions_info[c_i['wyId']]=c_i
        if c_i['wyId'] not in competition_list:
            competition_list.append(c_i['wyId'])

    return [competitions_info[c] for c in competition_list]