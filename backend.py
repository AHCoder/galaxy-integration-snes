import json
import os
import time
import urllib.parse
import urllib.request

import user_config
from definitions import SNESGame
from galaxy.api.types import LocalGame, LocalGameState

QUERY_URL = "https://www.giantbomb.com/api/search/?api_key={}&field_list=id,name&format=json&limit=1&query={}&resources=game"

class BackendClient:
    def __init__(self):
        self.games = []
        self.roms = {}
        self.start_time = 0
        self.end_time = 0


    def _get_games_giant_bomb(self) -> list:
        ''' Returns a list of SNESGame objects with id, name, and path

        Used if the user chooses to pull from Giant Bomb database
        The first result is used and only call for id and name, in json format, limited to 1 result
        '''
        self._get_rom_names()

        for rom in self.roms:
            url = QUERY_URL.format(user_config.api_key, urllib.parse.quote(rom))            
            with urllib.request.urlopen(url) as response:
                search_results = json.loads(response.read())

            id = search_results["results"][0]["id"]
            name = search_results["results"][0]["name"]
            self.games.append(
                SNESGame(
                    str(id),
                    str(name),
                    str(self.roms.get(rom))
                )
            )

        return self.games


    def _get_rom_names(self) -> None:
        ''' Returns none
        
        Adds the rom name and path to the roms dict
        '''        
        for root, dirs, files in os.walk(user_config.roms_path):
            for file in files:
               if file.lower().endswith((".sfc", ".smc")):
                    name = os.path.splitext(os.path.basename(file))[0] # Split name of file from it's path/extension
                    path = os.path.join(root, file)
                    self.roms[name] = path


    def _get_state_changes(self, old_list, new_list) -> list:
        old_dict = {x.game_id: x.local_game_state for x in old_list}
        new_dict = {x.game_id: x.local_game_state for x in new_list}
        result = []
        # removed games
        result.extend(LocalGame(id, LocalGameState.None_) for id in old_dict.keys() - new_dict.keys())
        # added games
        result.extend(local_game for local_game in new_list if local_game.game_id in new_dict.keys() - old_dict.keys())
        # state changed
        result.extend(
            LocalGame(id, new_dict[id]) for id in new_dict.keys() & old_dict.keys() if new_dict[id] != old_dict[id]
            )
        return result

    def _set_session_start(self) -> None:
        ''' Sets the session start to the current time'''
        self.start_time = time.time()


    def _set_session_end(self) -> None:
        ''' Sets the session end to the current time'''
        self.end_time = time.time()


    def _get_session_duration(self) -> int:
        ''' Returns the duration of the game session in minutes as an int'''
        return int(round((self.end_time - self.start_time) / 60))
