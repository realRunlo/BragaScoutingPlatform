import requests
from bs4 import BeautifulSoup
import json
import argparse
import math
import os
import time


market_value = {}
headers = {'User-Agent': 
               'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}

def parse_arguments():
    '''Define and parse arguments using argparse'''
    parser = argparse.ArgumentParser(description='Transfermarkt Scraper')
    parser.add_argument('--output','-o'            ,type=str, nargs=1,required=True                                , help='Output json file path')
    parser.add_argument('--leaguename','-ln'            ,type=str, nargs=1,required=False                                , help='League Name ex: laliga/liganos/premier-league')
    parser.add_argument('--leaguecode','-lc'            ,type=str, nargs=1,required=False                                , help='League Code ex: ES1/ES2/PO1')
    parser.add_argument('--numberpages','-np'            ,type=int, nargs=1,required=False                                , help='Number of pages to scrap')
    parser.add_argument('--requestfile','-rf'           ,type=str, nargs=1,required=False                                   , help='Reuqest file' )
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_arguments()
    #number_pages = 22
    #league = "laliga"
    #league_code = "ES2"
    #filename = "market_values_es2.json"

    #if args.requestfile[0].endswith('.json'):
    competitions = []
    filename = args.output[0]

    if args.requestfile != None:
        request_file_path = args.requestfile[0]
        if request_file_path.endswith('.json') and os.path.exists(request_file_path):
            competitions = json.load(open(request_file_path))
            competitions = competitions['competitions']
        else:
            print("Error")
    else:
        if(args.leaguename != None):
            league_name = args.leaguename[0]
        else:
            print("Error")
        if(args.leaguecode != None):
            league_code = args.leaguecode[0]
        else:
            print("Error")

        competition = {
                "league_name" : league_name,
                "league_code" : league_code,
        }

        if(args.numberpages != None):
            number_pages = args.numberpages[0]
            competition['number_pages'] = number_pages
        
        competitions.append(competition)
    
    for competition in competitions:
        if not('number_pages' in competition):
            league_name = competition['league_name']
            league_code = competition['league_code']
            
            page = f"https://www.transfermarkt.co.uk/{league_name}/marktwertaenderungen/wettbewerb/{league_code}"
            pageTree = requests.get(page, headers=headers)
            pageSoup = BeautifulSoup(pageTree.content, 'html.parser')

            header = pageSoup.find("header", {"class" : "data-header"})
            info_box = header.find("div",{"class":"data-header__info-box"})
            header_items = info_box.findAll("ul",{"class" : "data-header__items"})[0]
            header_label = header_items.findAll("li",{"class" : "data-header__label"})[1]
            number_players = int(header_label.find("span").text)
            number_pages = math.ceil(number_players/25)
            competition['number_pages'] = number_pages
        market_value = {league_code : {}}

    start_time = time.time()
    for competition in competitions:
        comp_start_time = time.time()
        league = {}
        league_name = competition['league_name']
        league_code = competition['league_code']
        number_pages = competition['number_pages']
        print("Scraping " + league_name)
        for i in range(number_pages):
            print(f"Scraping page {i+1}/{number_pages}")
            page = f"https://www.transfermarkt.co.uk/{league_name}/marktwertaenderungen/wettbewerb/{league_code}/page/{i+1}"
            pageTree = requests.get(page, headers=headers)
            pageSoup = BeautifulSoup(pageTree.content, 'html.parser')
            table = pageSoup.find("table", {"class" : "items"})
            tbody = table.find("tbody")
            trseven = tbody.findAll("tr", {"class" : "even"})
            trsodd = tbody.findAll("tr", {"class" : "odd"})
            for tr in trseven + trsodd:
                price = tr.findAll("td")[5].get_text(strip=True)
                name = tr.find("table", {"class" : "inline-table"})
                name = name.find("td",{"class" : "hauptlink"}).text[1:-1]
                club = tr.find("td", {"class" : "zentriert"}).find("a")['title']
                if not club in league:  
                    league[club] = {}
                league[club][name]= price

        market_value[league_code] = league
        print(f"Scraped {league_name} in {time.time()-comp_start_time} secs.\n")
    print(f"Scraped all in {time.time()-start_time} secs.")
    # Serializing json   
    json_object = json.dumps(market_value, indent = 4)  
    f = open(filename, "w")
    f.write(json_object)
    f.close()