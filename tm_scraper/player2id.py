import os
import sys
import argparse
from db import Db_handler

if __name__ == '__main__':
    player_name = "Jasper Cillessen"
    db_cred_path = "cred.json"
    player_team = "" 

    db_handler = Db_handler(config_json=db_cred_path,logger=None)
    db_handler.create_connection()
    if db_handler.connection:
        # Because spacing in db and tm is not consistent
        spacedout_player_name = player_name.replace(' ','%')

        where_statement="where name like '" + spacedout_player_name + "' or short_name like '" + spacedout_player_name + "'"
        db_players = db_handler.select('player','idplayer,current_team',where_statement)
        
        # full match
        if len(db_players) == 1:
            print("Player id: ",db_players[0][0])
        elif len(db_players >1):
            for player in db_players:       
                # Use jelly fish to compare team names
                if team==player[1]:
                    print("Player id", player[0])
                    break
        else:
            print("Player not in db")
    else:
        print('DB connection failed to be established.')
