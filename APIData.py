import os.path

import pandas as pd
from nba_api.stats.endpoints import LeagueDashTeamStats, LeagueDashPlayerStats, PlayerDashboardByYearOverYear, \
    CommonPlayerInfo, PlayerDashboardByOpponent, PlayerDashboardByLastNGames, PlayerDashboardByGeneralSplits, \
    PlayerGameLog, LeagueGameLog, TeamYearByYearStats, CommonAllPlayers, LeagueGameFinder
from nba_api.stats.library.parameters import Season, SeasonYear, SeasonSegment
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playerdashboardbylastngames, playerdashboardbygeneralsplits, \
    playerdashboardbyopponent
from nba_api.stats.endpoints import commonallplayers, playergamelog
from ast import literal_eval
import time
import random
import json



def get_team_nickname(player_name, season):
    # Get player ID
    player = [p for p in players.get_players() if p['full_name'] == player_name][0]
    player_id = player['id']

    # Get all games for the specified season and player
    game_finder = LeagueGameFinder(player_or_team_abbreviation='P', player_id_nullable=player_id, season_nullable=season, season_type_nullable='Regular Season')
    games = game_finder.get_data_frames()[0]

    # Get the team ID for the first game the player played in during the season
    try:
        team_id = games.iloc[0]["TEAM_ID"]

        # Get the team nickname for the specified team ID
        team_nickname = [team['nickname'] for team in teams.get_teams() if team['id'] == team_id][0]

        return team_nickname
    except IndexError:
        return None


def get_player_seasons(player_name):
    # Find player_id
    players_local = CommonAllPlayers()
    players_df = players_local.get_data_frames()[0]
    player_id = players_df.loc[players_df['DISPLAY_FIRST_LAST'] == player_name]['PERSON_ID'].values[0]

    # Get player's seasons
    from_year = 1946  # NBA's first season
    to_year = 2022  # Current year's season
    seasons = []
    for year in range(from_year, to_year):
        player_seasons = CommonAllPlayers(is_only_current_season=0, season=year).get_data_frames()[0]
        if not player_seasons[player_seasons['PERSON_ID'] == player_id].empty:
            seasons.append(str(year) + '-' + str(year + 1)[-2:])

    return seasons


# Get player ID by player name
def get_player_id(player_name):
    player_dict = players.get_players()
    for player in player_dict:
        if player['full_name'].lower() == player_name.lower():
            return player['id']


# Get team ID by team name
def get_team_id(team_name):
    team_dict = teams.get_teams()
    for team in team_dict:
        if team['nickname'].lower() == team_name.lower() or team['abbreviation'].lower() == team_name.lower() or \
                team['full_name'].lower() == team_name.lower():
            return team['id']


def get_nickname_from_abbrv(abbrv):
    team_dict = teams.get_teams()
    for team in team_dict:
        if team['abbreviation'].lower() == abbrv.lower():
            return team['nickname']


def get_player_team(player_name):
    # Get the player's ID
    player = [p for p in players.get_players() if p['full_name'] == player_name][0]
    player_id = player['id']

    # Create a CommonPlayerInfo endpoint instance
    player_info = CommonPlayerInfo(player_id=player_id)

    # Get the player's team name and ID
    index = player_info.common_player_info.get_dict()["headers"].index("TEAM_NAME")
    team_name = player_info.common_player_info.get_dict()["data"][0][index]

    return team_name


def get_past_5_seasons(season):
    curr_year = season
    seasons = []

    for _ in range(5):
        seasons.append(f"{curr_year - 1}-{str(curr_year)[2:]}")
        curr_year -= 1

    return seasons

def get_players_on_team(team_name):
    team_players = commonallplayers.CommonAllPlayers(is_only_current_season=1)
    team_players_response = team_players.get_data_frames()[0]
    players = team_players_response[team_players_response.TEAM_NAME == team_name]
    return players['DISPLAY_FIRST_LAST'].tolist()

def get_player_info(player):
    player_id = get_player_id(player)
    player_info = CommonPlayerInfo(player_id=player_id)
    player_info_response = player_info.get_data_frames()[0]

    height = player_info_response.loc[0, 'HEIGHT']
    weight = player_info_response.loc[0, 'WEIGHT']
    jersey_number = player_info_response.loc[0, 'JERSEY']
    position = player_info_response.loc[0, 'POSITION']
    team = get_player_team(player)
    
    player_stats = PlayerDashboardByYearOverYear(player_id=player_id)
    player_stats_response = player_stats.get_data_frames()[0]
    
    true_shooting_percentage = player_stats_response.loc[0, 'FG_PCT']
    
    return {"Team": team, "Abbrv": get_team_abbrv(team), "Height": height, "Weight": weight, "#": jersey_number, "POS": position, "TS": true_shooting_percentage}

def get_past_10_seasons(season):
    curr_year = season
    seasons = []

    for _ in range(10):
        seasons.append(f"{curr_year - 1}-{str(curr_year)[2:]}")
        curr_year -= 1

    return seasons


def get_team_abbrv(team_name):
    team_dict = teams.get_teams()
    for team in team_dict:
        if team['nickname'].lower() == team_name.lower() or team['full_name'].lower() == team_name.lower():
            return team['abbreviation']


def build_team_data_dict():
    all_teams = [team["nickname"] for team in teams.get_teams()]


    data = {}
    for team in all_teams:
        abbrv = get_team_abbrv(team)
        data[team] = {"abbrv": abbrv, "id": get_team_id(team), "nickname": get_nickname_from_abbrv(abbrv)}
        data[abbrv] = {"id": get_team_id(team), "nickname": get_nickname_from_abbrv(abbrv)}

    with open("team_data.json", "w") as data_fp:
        json.dump(data, data_fp)


def load_data_dict():
    if not os.path.exists("team_data.json"):
        build_team_data_dict()
        
    with open("team_data.json", "r") as data_fp:
        return json.load(data_fp)


def save_cache(player_name, cache, name):
    if not os.path.exists(f"{player_name}_caches/"):
        os.mkdir(f"{player_name}_caches/")

    with open(os.path.join(f"{player_name}_caches", name + ".json"), "w") as c:
        cache_json = serialize_dict({str(k): v for k, v in cache.items()})
        json.dump(cache_json, c)


def save_partial_cache(player_name, cache, name, number):
    loaded_number = -1

    if os.path.exists(os.path.join(f"{player_name}_partial_caches", f"{name}_PARTIAL" + ".txt")):
        with open(os.path.join(f"{player_name}_partial_caches", f"{name}_PARTIAL" + ".txt"), "r") as cnum:
            loaded_number = int(cnum.read())

    if number <= loaded_number:
        return

    if not os.path.exists(f"{player_name}_partial_caches/"):
        os.mkdir(f"{player_name}_partial_caches/")

    with open(os.path.join(f"{player_name}_partial_caches", f"{name}_PARTIAL" + ".json"), "w") as c:
        json_cache = serialize_dict({str(k): v for k, v in cache.items()})
        json.dump(json_cache, c)

    with open(os.path.join(f"{player_name}_partial_caches", f"{name}_PARTIAL" + ".txt"), "w") as cnum:
        cnum.write(str(number))


def load_cache(player_name, name):
    path = os.path.join(f"{player_name}_caches", name + ".json")

    if not os.path.exists(path):
        return load_partial_cache(player_name, name)

    with open(path, "r") as c:
        if "def" in path:
            return {literal_eval(k): v for k, v in json.load(c).items()}, 0
        else:
            return {k: v for k, v in json.load(c).items()}, 0


def load_partial_cache(player_name, name):
    if os.path.exists(os.path.join(f"{player_name}_partial_caches", f"{name}_PARTIAL" + ".txt")):
        num = 0
        with open(os.path.join(f"{player_name}_partial_caches", f"{name}_PARTIAL" + ".txt"), "r") as cnum:
            num = int(cnum.read())

        with open(os.path.join(f"{player_name}_partial_caches", f"{name}_PARTIAL" + ".json"), "r") as c:
            if name != "def_ranking_cache":
                return json.load(c), num

            return {literal_eval(k): v for k, v in json.load(c).items()}, num

    return dict(), 0


def serialize_dict(d):
    return {k: float(v) for k, v in d.items()}


class APIData:

    def __init__(self, player_name, season):
        self.team_data = load_data_dict()
        self.all_teams = [team["nickname"] for team in teams.get_teams()]

        random.shuffle(self.all_teams)  # introduce some randomness for better spread in data

        self.player_name = player_name
        self.player = get_player_id(self.player_name)
        self.opposing_team_name = self.all_teams[0]
        self.opponent = self.team_data[self.opposing_team_name]["id"]
        self.team = get_player_team(player_name)
        self.team_id = self.team_data[self.team]["id"]
        self.seasons = get_past_5_seasons(season)
        self.opp_team_abbrv = self.team_data[self.opposing_team_name]["abbrv"]
        self.season = "2022-23"
        self.create_caches = False
        self.player_stats = playerdashboardbygeneralsplits.PlayerDashboardByGeneralSplits(player_id=self.player,
                                                                                     season=self.season,
                                                                                     per_mode_detailed='PerGame').get_data_frames()[
            0]
        self.player_stats_opp = None
        self.player_game_logs = self._get_player_game_logs()

    def _get_player_game_logs(self):
        if os.path.exists(f"{self.player_name}_full_game_logs.json"):
            with open(f"{self.player_name}_full_game_logs.json", "r") as data:
                return {k: pd.DataFrame(v) for k, v in json.load(data).items()}

        d = {}
        for season in self.seasons:
            d[season] = PlayerGameLog(player_id=self.player, season=season).get_data_frames()[0]

        if self.create_caches:
            with open(f"{self.player_name}_full_game_logs.json", "w") as data:
                json.dump({k: v.to_dict() for k, v in d.items()}, data)

        return d

    def get_formatted_game_logs(self):
        raw_data = self.player_game_logs
        db_formatted_data = []

        for year, df in raw_data.items():
            for row in df.itertuples(index=False, name=None):
                db_formatted_data.append((self.player_name, year, row[4].split(" ")[-1], row[-3], row[-9], row[-8]))

        return db_formatted_data

    def get_opp_defensive_ranking(self):
        print("Getting Defensive Ranking")
        time.sleep(0.6)
        team_stats = TeamYearByYearStats(team_id=self.opponent)
        team_stats_df = team_stats.get_data_frames()[0]
        team_stats_season_df = team_stats_df.loc[team_stats_df['YEAR'] == self.season]
        defensive_ranking = team_stats_season_df['PTS_RANK'].values[0]
        return defensive_ranking

    def season_avg_ppg(self):
        print("Getting Season PPG")
        
        return self.player_stats['PTS'][0]

    def season_avg_rpg(self):
        print("Getting Season RPG")
        
        return self.player_stats['REB'][0]

    def season_avg_apg(self):
        print("Getting Season APG")
        
        return self.player_stats['AST'][0]

    def past5_seasons_avg_ppg(self):
        print("Getting Past 5 Season PPG")
        time.sleep(0.6)
        gp = 0
        tp = 0
        for season in self.seasons:
            game_log = self.player_game_logs[season]

            # Calculate games played and total points
            gp += len(game_log)
            tp += game_log['PTS'].sum()

        return round(tp / gp, 1)

    def past5_seasons_avg_rpg(self):
        print("Getting Past 5 Season RPG")
        time.sleep(0.6)
        gp = 0
        tp = 0
        for season in self.seasons:
            game_log = self.player_game_logs[season]

            # Calculate games played and total points
            gp += len(game_log)
            tp += game_log['REB'].sum()

        return round(tp / gp, 1)

    def past5_seasons_avg_apg(self):
        print("Getting Past 5 Season APG")
        time.sleep(0.6)
        gp = 0
        tp = 0
        for season in self.seasons:
            game_log = self.player_game_logs[season]

            # Calculate games played and total points
            gp += len(game_log)
            tp += game_log['AST'].sum()

        return round(tp / gp, 1)

    def past5_seasons_avg_ppg_vs_opp(self):
        print("Getting Past 5 Season PPG vs opp")
        time.sleep(0.6)
        # Get splits data for the past 5 seasons
        gp = 0
        tp = 0
        for season in self.seasons:
            game_log = self.player_game_logs[season]
            game_log["MATCHUP"] = game_log["MATCHUP"].astype("string")
            game_log_vs_opponent = game_log.loc[game_log["MATCHUP"].str.contains(str(self.opp_team_abbrv))]
            # Calculate games played and total points
            gp += len(game_log_vs_opponent)
            tp += game_log_vs_opponent['PTS'].sum()
        return round(tp / gp, 1)

    def past5_seasons_avg_rpg_vs_opp(self):
        print("Getting Past 5 Season RPG vs opp")
        time.sleep(0.6)
        gp = 0
        tp = 0
        for season in self.seasons:
            game_log = self.player_game_logs[season]
            game_log["MATCHUP"] = game_log["MATCHUP"].astype("string")
            game_log_vs_opponent = game_log.loc[game_log["MATCHUP"].str.contains(str(self.opp_team_abbrv))]
            # Calculate games played and total points
            gp += len(game_log_vs_opponent)
            tp += game_log_vs_opponent['REB'].sum()
        return round(tp / gp, 1)

    def past5_seasons_avg_apg_vs_opp(self):
        print("Getting Past 5 Season APG vs opp")
        time.sleep(0.6)
        gp = 0
        tp = 0
        for season in self.seasons:
            game_log = self.player_game_logs[season]
            game_log["MATCHUP"] = game_log["MATCHUP"].astype("string")
            game_log_vs_opponent = game_log.loc[game_log["MATCHUP"].str.contains(str(self.opp_team_abbrv))]
            # Calculate games played and total points
            gp += len(game_log_vs_opponent)
            tp += game_log_vs_opponent['AST'].sum()
        return round(tp / gp, 1)

    def season_avg_ppg_vs_opp(self):
        print("Getting Season PPG vs opp")
        time.sleep(0.6)
        self.player_stats_opp = \
            playerdashboardbyopponent.PlayerDashboardByOpponent(player_id=self.player, opponent_team_id=self.opponent,
                                                                per_mode_detailed='PerGame').get_data_frames()[0]
        try:
            return self.player_stats_opp['PTS'][0]
        except IndexError:
            return 0.0

    def season_avg_rpg_vs_opp(self):
        print("Getting Season RPG vs opp")
        
        try:
            return self.player_stats_opp['REB'][0]
        except IndexError:
            return 0.0

    def season_avg_apg_vs_opp(self):
        print("Getting Season APG vs opp")
        
        try:
            return self.player_stats_opp['AST'][0]
        except IndexError:
            return 0.0

    def get_past5_season_stats(self):
        data = []
        for season in self.seasons:
            splits = playerdashboardbygeneralsplits.PlayerDashboardByGeneralSplits(player_id=self.player,
                                                                                        season=season,
                                                                                        per_mode_detailed='PerGame').get_data_frames()[
                0]
            try:
                data.append((self.player_name, season, splits["PTS"][0], splits["REB"][0], splits["AST"][0], splits["GP"][0]))
            except Exception as e:
                continue
        
        return data

    def create_dataset(self):
        # collect games
        games = {}
        games_collected = 0
        team_idx = 0

        if os.path.exists(f"{self.player_name}_save_gamelog.json"):
            with open(f"{self.player_name}_save_gamelog.json", "r") as log:
                games = json.load(log)
                games = {literal_eval(k): pd.DataFrame(v) for k, v in games.items()}
        else:
            # Remove teams played on at time (not perfect but minimizes API calls)
            removed = []
            for season in self.seasons:
                team_on_at_time = get_team_nickname(self.player_name, season)

                if team_on_at_time and team_on_at_time not in removed:
                    self.all_teams.remove(team_on_at_time)
                    removed.append(team_on_at_time)
                time.sleep(0.3)

            np_seasons = []  # TODO: FINISH NOT PLAYED SEASONS
            while games_collected < 120 or team_idx == len(self.all_teams)-1:
                if team_idx > 12:
                    break
                for season in self.seasons:
                    game_log = self.player_game_logs[season]
                    game_log["MATCHUP"] = game_log["MATCHUP"].astype("string")
                    game_log_vs_opponent = game_log.loc[game_log["MATCHUP"].str.contains(str(self.opp_team_abbrv))]

                    if len(game_log_vs_opponent) > 0:
                        games[(season, self.opp_team_abbrv)] = game_log_vs_opponent
                        games_collected += len(game_log_vs_opponent.index)

                    time.sleep(0.6)

                print(games_collected, team_idx)
                self.opposing_team_name = self.all_teams[team_idx]
                self.opponent = self.team_data[self.opposing_team_name]["id"]
                self.opp_team_abbrv = self.team_data[self.opposing_team_name]["abbrv"]
                team_idx += 1
            
            if games_collected < 120:
                return
            
            for season in np_seasons:
                self.seasons.remove(season)

            with open(f"{self.player_name}_save_gamelog.json", "w") as log:
                json_games = {str(k): v.to_dict() for k, v in games.items()}
                json.dump(json_games, log)

        training_set = []

        if os.path.exists(f"{self.player_name}_saved_gamedata.json"):
            with open(f"{self.player_name}_saved_gamedata.json", "r") as data:
                training_set = json.load(data)
        else:
            # caches
            def_ranking_cache, index = load_cache(self.player_name, "def_ranking_cache")
            season_ppg_cache, _ = load_cache(self.player_name, "season_ppg_cache")
            season_rpg_cache, _ = load_cache(self.player_name, "season_rpg_cache")
            season_apg_cache, _ = load_cache(self.player_name, "season_apg_cache")
            p5_season_ppg_cache, _ = load_cache(self.player_name, "p5_season_ppg_cache")
            p5_season_apg_cache, _ = load_cache(self.player_name, "p5_season_apg_cache")
            p5_season_rpg_cache, _ = load_cache(self.player_name, "p5_season_rpg_cache")
            p5_season_ppg_vs_opp_cache, _ = load_cache(self.player_name, "p5_season_ppg_vs_opp_cache")
            p5_season_apg_vs_opp_cache, _ = load_cache(self.player_name, "p5_season_apg_vs_opp_cache")
            p5_season_rpg_vs_opp_cache, _ = load_cache(self.player_name, "p5_season_rpg_vs_opp_cache")
            season_ppg_vs_opp_cache, _ = load_cache(self.player_name, "season_ppg_vs_opp_cache")
            season_apg_vs_opp_cache, _ = load_cache(self.player_name, "season_apg_vs_opp_cache")
            season_rpg_vs_opp_cache, _ = load_cache(self.player_name, "season_rpg_vs_opp_cache")

            if not os.path.exists(f"{self.player_name}_caches"):
                # fill caches
                data_to_del = []
                for k in games:
                    if index == len(self.seasons):
                        break

                    row = games[k].iloc[0]
                    game_data = {"PTS": float(row["PTS"]), "REB": float(row["REB"]), "AST": float(row["AST"])}
                    data_to_del.append(k)

                    self.season, self.opp_team_abbrv = k
                    self.opposing_team_name = self.team_data[self.opp_team_abbrv]["nickname"]
                    self.opponent = self.team_data[self.opposing_team_name]["id"]
                    self.seasons = get_past_5_seasons(int("20" + self.season[-2:]))

                    def_ranking = self.get_opp_defensive_ranking()
                    def_ranking_cache[(self.opp_team_abbrv, self.season)] = def_ranking
                    season_ppg = self.season_avg_ppg()
                    season_ppg_cache[self.season] = season_ppg
                    season_apg = self.season_avg_apg()
                    season_apg_cache[self.season] = season_apg
                    season_rpg = self.season_avg_rpg()
                    season_rpg_cache[self.season] = season_rpg
                    p5_season_ppg = self.past5_seasons_avg_ppg()
                    p5_season_ppg_cache[self.season] = p5_season_ppg
                    p5_season_apg = self.past5_seasons_avg_apg()
                    p5_season_apg_cache[self.season] = p5_season_apg
                    p5_season_rpg = self.past5_seasons_avg_rpg()
                    p5_season_rpg_cache[self.season] = p5_season_rpg
                    p5_season_ppg_vs_opp = self.past5_seasons_avg_ppg_vs_opp()
                    p5_season_ppg_vs_opp_cache[self.season] = p5_season_ppg_vs_opp
                    p5_season_apg_vs_opp = self.past5_seasons_avg_apg_vs_opp()
                    p5_season_apg_vs_opp_cache[self.season] = p5_season_apg_vs_opp
                    p5_season_rpg_vs_opp = self.past5_seasons_avg_rpg_vs_opp()
                    p5_season_rpg_vs_opp_cache[self.season] = p5_season_rpg_vs_opp
                    season_ppg_vs_opp = self.season_avg_ppg_vs_opp()
                    season_ppg_vs_opp_cache[self.season] = season_ppg_vs_opp
                    season_apg_vs_opp = self.season_avg_apg_vs_opp()
                    season_apg_vs_opp_cache[self.season] = season_apg_vs_opp
                    season_rpg_vs_opp = self.season_avg_rpg_vs_opp()
                    season_rpg_vs_opp_cache[self.season] = season_rpg_vs_opp

                    predicting_factors = {
                        "Opponent Def. Ranking": float(def_ranking),
                        "Season PPG": float(season_ppg),
                        "Season APG": float(season_apg),
                        "Season RPG": float(season_rpg),
                        "P5 Season PPG": float(p5_season_ppg),
                        "P5 Season APG": float(p5_season_apg),
                        "P5 Season RPG": float(p5_season_rpg),
                        "P5 Season PPG vs OPP": float(p5_season_ppg_vs_opp),
                        "P5 Season APG vs OPP": float(p5_season_apg_vs_opp),
                        "P5 Season RPG vs OPP": float(p5_season_rpg_vs_opp),
                        "Season PPG vs OPP": float(season_ppg_vs_opp),
                        "Season APG vs OPP": float(season_apg_vs_opp),
                        "Season RPG vs OPP": float(season_rpg_vs_opp),
                    }

                    # saving partial caches
                    if index > -1:  # if statement so I can close this code block
                        save_partial_cache(self.player_name, def_ranking_cache, "def_ranking_cache", index)
                        save_partial_cache(self.player_name, season_ppg_cache, "season_ppg_cache", index)
                        save_partial_cache(self.player_name, season_rpg_cache, "season_rpg_cache", index)
                        save_partial_cache(self.player_name, season_apg_cache, "season_apg_cache", index)
                        save_partial_cache(self.player_name, p5_season_ppg_cache, "p5_season_ppg_cache", index)
                        save_partial_cache(self.player_name, p5_season_apg_cache, "p5_season_apg_cache", index)
                        save_partial_cache(self.player_name, p5_season_rpg_cache, "p5_season_rpg_cache", index)
                        save_partial_cache(self.player_name, p5_season_ppg_vs_opp_cache, "p5_season_ppg_vs_opp_cache",
                                           index)
                        save_partial_cache(self.player_name, p5_season_apg_vs_opp_cache, "p5_season_apg_vs_opp_cache",
                                           index)
                        save_partial_cache(self.player_name, p5_season_rpg_vs_opp_cache, "p5_season_rpg_vs_opp_cache",
                                           index)
                        save_partial_cache(self.player_name, season_ppg_vs_opp_cache, "season_ppg_vs_opp_cache", index)
                        save_partial_cache(self.player_name, season_apg_vs_opp_cache, "season_apg_vs_opp_cache", index)
                        save_partial_cache(self.player_name, season_rpg_vs_opp_cache, "season_rpg_vs_opp_cache", index)

                    index += 1
                    print(f"Filling Cache Progress: {index}/{len(self.seasons)}")
                    training_set.append((predicting_factors, game_data))

                for k in data_to_del:
                    del games[k]

                save_cache(self.player_name, def_ranking_cache, "def_ranking_cache")
                save_cache(self.player_name, season_ppg_cache, "season_ppg_cache")
                save_cache(self.player_name, season_rpg_cache, "season_rpg_cache")
                save_cache(self.player_name, season_apg_cache, "season_apg_cache")
                save_cache(self.player_name, p5_season_ppg_cache, "p5_season_ppg_cache")
                save_cache(self.player_name, p5_season_apg_cache, "p5_season_apg_cache")
                save_cache(self.player_name, p5_season_rpg_cache, "p5_season_rpg_cache")
                save_cache(self.player_name, p5_season_ppg_vs_opp_cache, "p5_season_ppg_vs_opp_cache")
                save_cache(self.player_name, p5_season_apg_vs_opp_cache, "p5_season_apg_vs_opp_cache")
                save_cache(self.player_name, p5_season_rpg_vs_opp_cache, "p5_season_rpg_vs_opp_cache")
                save_cache(self.player_name, season_ppg_vs_opp_cache, "season_ppg_vs_opp_cache")
                save_cache(self.player_name, season_apg_vs_opp_cache, "season_apg_vs_opp_cache")
                save_cache(self.player_name, season_rpg_vs_opp_cache, "season_rpg_vs_opp_cache")

            index = 0
            for k, v in games.items():
                for _, row in v.iterrows():
                    # change internal parameters for API requests
                    self.season, self.opp_team_abbrv = k
                    self.opposing_team_name = self.team_data[self.opp_team_abbrv]["nickname"]
                    self.opponent = self.team_data[self.opposing_team_name]["id"]
                    self.seasons = get_past_5_seasons(int("20" + self.season[-2:]))
                    game_data = {"PTS": float(row["PTS"]), "REB": float(row["REB"]), "AST": float(row["AST"])}

                    print(season_ppg_cache, self.season)

                    if not def_ranking_cache.get((self.opp_team_abbrv, self.season)):
                        def_ranking = self.get_opp_defensive_ranking()
                        def_ranking_cache[(self.opp_team_abbrv, self.season)] = def_ranking
                    else:
                        print("Using Cache")
                        def_ranking = def_ranking_cache[(self.opp_team_abbrv, self.season)]
                    if not season_ppg_cache.get(self.season):
                        season_ppg = self.season_avg_ppg()
                        season_ppg_cache[self.season] = season_ppg
                    else:
                        print("Using Cache")
                        season_ppg = season_ppg_cache[self.season]
                    if not season_apg_cache.get(self.season):
                        season_apg = self.season_avg_apg()
                        season_apg_cache[self.season] = season_apg
                    else:
                        print("Using Cache")
                        season_apg = season_apg_cache[self.season]
                    if not season_rpg_cache.get(self.season):
                        season_rpg = self.season_avg_rpg()
                        season_rpg_cache[self.season] = season_rpg
                    else:
                        print("Using Cache")
                        season_rpg = season_rpg_cache[self.season]
                    if not p5_season_ppg_cache.get(self.season):
                        p5_season_ppg = self.past5_seasons_avg_ppg()
                        p5_season_ppg_cache[self.season] = p5_season_ppg
                    else:
                        print("Using Cache")
                        p5_season_ppg = p5_season_ppg_cache[self.season]
                    if not p5_season_apg_cache.get(self.season):
                        p5_season_apg = self.past5_seasons_avg_apg()
                        p5_season_apg_cache[self.season] = p5_season_apg
                    else:
                        print("Using Cache")
                        p5_season_apg = p5_season_apg_cache[self.season]
                    if not p5_season_rpg_cache.get(self.season):
                        p5_season_rpg = self.past5_seasons_avg_rpg()
                        p5_season_rpg_cache[self.season] = p5_season_rpg
                    else:
                        print("Using Cache")
                        p5_season_rpg = p5_season_rpg_cache[self.season]
                    if not p5_season_ppg_vs_opp_cache.get(self.season):
                        p5_season_ppg_vs_opp = self.past5_seasons_avg_ppg_vs_opp()
                        p5_season_ppg_vs_opp_cache[self.season] = p5_season_ppg_vs_opp
                    else:
                        print("Using Cache")
                        p5_season_ppg_vs_opp = p5_season_ppg_vs_opp_cache[self.season]
                    if not p5_season_apg_vs_opp_cache.get(self.season):
                        p5_season_apg_vs_opp = self.past5_seasons_avg_apg_vs_opp()
                        p5_season_apg_vs_opp_cache[self.season] = p5_season_apg_vs_opp
                    else:
                        print("Using Cache")
                        p5_season_apg_vs_opp = p5_season_apg_vs_opp_cache[self.season]
                    if not p5_season_rpg_vs_opp_cache.get(self.season):
                        p5_season_rpg_vs_opp = self.past5_seasons_avg_rpg_vs_opp()
                        p5_season_rpg_vs_opp_cache[self.season] = p5_season_rpg_vs_opp
                    else:
                        print("Using Cache")
                        p5_season_rpg_vs_opp = p5_season_rpg_vs_opp_cache[self.season]
                    if not season_ppg_vs_opp_cache.get(self.season):
                        season_ppg_vs_opp = self.season_avg_ppg_vs_opp()
                        season_ppg_vs_opp_cache[self.season] = season_ppg_vs_opp
                    else:
                        print("Using Cache")
                        season_ppg_vs_opp = season_ppg_vs_opp_cache[self.season]
                    if not season_apg_vs_opp_cache.get(self.season):
                        season_apg_vs_opp = self.season_avg_apg_vs_opp()
                        season_apg_vs_opp_cache[self.season] = season_apg_vs_opp
                    else:
                        print("Using Cache")
                        season_apg_vs_opp = season_apg_vs_opp_cache[self.season]
                    if not season_rpg_vs_opp_cache.get(self.season):
                        season_rpg_vs_opp = self.season_avg_rpg_vs_opp()
                        season_rpg_vs_opp_cache[self.season] = season_rpg_vs_opp
                    else:
                        print("Using Cache")
                        season_rpg_vs_opp = season_rpg_vs_opp_cache[self.season]
                    predicting_factors = {
                        "Opponent Def. Ranking": float(def_ranking),
                        "Season PPG": float(season_ppg),
                        "Season APG": float(season_apg),
                        "Season RPG": float(season_rpg),
                        "P5 Season PPG": float(p5_season_ppg),
                        "P5 Season APG": float(p5_season_apg),
                        "P5 Season RPG": float(p5_season_rpg),
                        "P5 Season PPG vs OPP": float(p5_season_ppg_vs_opp),
                        "P5 Season APG vs OPP": float(p5_season_apg_vs_opp),
                        "P5 Season RPG vs OPP": float(p5_season_rpg_vs_opp),
                        "Season PPG vs OPP": float(season_ppg_vs_opp),
                        "Season APG vs OPP": float(season_apg_vs_opp),
                        "Season RPG vs OPP": float(season_rpg_vs_opp),
                    }
                    training_set.append((predicting_factors, game_data))

                index += 1
                print(f"{index}/{len(games)}")

            with open(f"{self.player_name}_saved_gamedata.json", "w") as data:
                json.dump(training_set, data)

        return training_set

    def set_opponent(self, opp_nick, season):
        self.opposing_team_name = opp_nick
        self.opponent = self.team_data[self.opposing_team_name]["id"]
        self.opp_team_abbrv = self.team_data[self.opposing_team_name]["abbrv"]
        self.season = f"{season-1}-{str(season)[-2:]}"

    def get_predicting_factors(self):
        def_ranking_cache, index = load_cache(self.player_name, "def_ranking_cache")
        season_ppg_cache, _ = load_cache(self.player_name, "season_ppg_cache")
        season_rpg_cache, _ = load_cache(self.player_name, "season_rpg_cache")
        season_apg_cache, _ = load_cache(self.player_name, "season_apg_cache")
        p5_season_ppg_cache, _ = load_cache(self.player_name, "p5_season_ppg_cache")
        p5_season_apg_cache, _ = load_cache(self.player_name, "p5_season_apg_cache")
        p5_season_rpg_cache, _ = load_cache(self.player_name, "p5_season_rpg_cache")
        p5_season_ppg_vs_opp_cache, _ = load_cache(self.player_name, "p5_season_ppg_vs_opp_cache")
        p5_season_apg_vs_opp_cache, _ = load_cache(self.player_name, "p5_season_apg_vs_opp_cache")
        p5_season_rpg_vs_opp_cache, _ = load_cache(self.player_name, "p5_season_rpg_vs_opp_cache")
        season_ppg_vs_opp_cache, _ = load_cache(self.player_name, "season_ppg_vs_opp_cache")
        season_apg_vs_opp_cache, _ = load_cache(self.player_name, "season_apg_vs_opp_cache")
        season_rpg_vs_opp_cache, _ = load_cache(self.player_name, "season_rpg_vs_opp_cache")

        if not def_ranking_cache.get((self.opp_team_abbrv, self.season)):
            def_ranking = self.get_opp_defensive_ranking()
            def_ranking_cache[(self.opp_team_abbrv, self.season)] = def_ranking
        else:
            print("Using Cache")
            def_ranking = def_ranking_cache[(self.opp_team_abbrv, self.season)]
        if not season_ppg_cache.get(self.season):
            season_ppg = self.season_avg_ppg()
            season_ppg_cache[self.season] = season_ppg
        else:
            print("Using Cache")
            season_ppg = season_ppg_cache[self.season]
        if not season_apg_cache.get(self.season):
            season_apg = self.season_avg_apg()
            season_apg_cache[self.season] = season_apg
        else:
            print("Using Cache")
            season_apg = season_apg_cache[self.season]
        if not season_rpg_cache.get(self.season):
            season_rpg = self.season_avg_rpg()
            season_rpg_cache[self.season] = season_rpg
        else:
            print("Using Cache")
            season_rpg = season_rpg_cache[self.season]
        if not p5_season_ppg_cache.get(self.season):
            p5_season_ppg = self.past5_seasons_avg_ppg()
            p5_season_ppg_cache[self.season] = p5_season_ppg
        else:
            print("Using Cache")
            p5_season_ppg = p5_season_ppg_cache[self.season]
        if not p5_season_apg_cache.get(self.season):
            p5_season_apg = self.past5_seasons_avg_apg()
            p5_season_apg_cache[self.season] = p5_season_apg
        else:
            print("Using Cache")
            p5_season_apg = p5_season_apg_cache[self.season]
        if not p5_season_rpg_cache.get(self.season):
            p5_season_rpg = self.past5_seasons_avg_rpg()
            p5_season_rpg_cache[self.season] = p5_season_rpg
        else:
            print("Using Cache")
            p5_season_rpg = p5_season_rpg_cache[self.season]
        if not p5_season_ppg_vs_opp_cache.get(self.season):
            p5_season_ppg_vs_opp = self.past5_seasons_avg_ppg_vs_opp()
            p5_season_ppg_vs_opp_cache[self.season] = p5_season_ppg_vs_opp
        else:
            print("Using Cache")
            p5_season_ppg_vs_opp = p5_season_ppg_vs_opp_cache[self.season]
        if not p5_season_apg_vs_opp_cache.get(self.season):
            p5_season_apg_vs_opp = self.past5_seasons_avg_apg_vs_opp()
            p5_season_apg_vs_opp_cache[self.season] = p5_season_apg_vs_opp
        else:
            print("Using Cache")
            p5_season_apg_vs_opp = p5_season_apg_vs_opp_cache[self.season]
        if not p5_season_rpg_vs_opp_cache.get(self.season):
            p5_season_rpg_vs_opp = self.past5_seasons_avg_rpg_vs_opp()
            p5_season_rpg_vs_opp_cache[self.season] = p5_season_rpg_vs_opp
        else:
            print("Using Cache")
            p5_season_rpg_vs_opp = p5_season_rpg_vs_opp_cache[self.season]
        if not season_ppg_vs_opp_cache.get(self.season):
            season_ppg_vs_opp = self.season_avg_ppg_vs_opp()
            season_ppg_vs_opp_cache[self.season] = season_ppg_vs_opp
        else:
            print("Using Cache")
            season_ppg_vs_opp = season_ppg_vs_opp_cache[self.season]
        if not season_apg_vs_opp_cache.get(self.season):
            season_apg_vs_opp = self.season_avg_apg_vs_opp()
            season_apg_vs_opp_cache[self.season] = season_apg_vs_opp
        else:
            print("Using Cache")
            season_apg_vs_opp = season_apg_vs_opp_cache[self.season]
        if not season_rpg_vs_opp_cache.get(self.season):
            season_rpg_vs_opp = self.season_avg_rpg_vs_opp()
            season_rpg_vs_opp_cache[self.season] = season_rpg_vs_opp
        else:
            print("Using Cache")
            season_rpg_vs_opp = season_rpg_vs_opp_cache[self.season]
        
        return {
            "Opponent Def. Ranking": float(def_ranking),
            "Season PPG": float(season_ppg),
            "Season APG": float(season_apg),
            "Season RPG": float(season_rpg),
            "P5 Season PPG": float(p5_season_ppg),
            "P5 Season APG": float(p5_season_apg),
            "P5 Season RPG": float(p5_season_rpg),
            "P5 Season PPG vs OPP": float(p5_season_ppg_vs_opp),
            "P5 Season APG vs OPP": float(p5_season_apg_vs_opp),
            "P5 Season RPG vs OPP": float(p5_season_rpg_vs_opp),
            "Season PPG vs OPP": float(season_ppg_vs_opp),
            "Season APG vs OPP": float(season_apg_vs_opp),
            "Season RPG vs OPP": float(season_rpg_vs_opp),
        }

    def get_predicting_factors_only_opp_data(self):
        p5_season_ppg_vs_opp_cache, _ = load_cache(self.player_name, "p5_season_ppg_vs_opp_cache")
        p5_season_apg_vs_opp_cache, _ = load_cache(self.player_name, "p5_season_apg_vs_opp_cache")
        p5_season_rpg_vs_opp_cache, _ = load_cache(self.player_name, "p5_season_rpg_vs_opp_cache")
        season_ppg_vs_opp_cache, _ = load_cache(self.player_name, "season_ppg_vs_opp_cache")
        season_apg_vs_opp_cache, _ = load_cache(self.player_name, "season_apg_vs_opp_cache")
        season_rpg_vs_opp_cache, _ = load_cache(self.player_name, "season_rpg_vs_opp_cache")

        if not p5_season_ppg_vs_opp_cache.get(self.season):
            p5_season_ppg_vs_opp = self.past5_seasons_avg_ppg_vs_opp()
            p5_season_ppg_vs_opp_cache[self.season] = p5_season_ppg_vs_opp
        else:
            print("Using Cache")
            p5_season_ppg_vs_opp = p5_season_ppg_vs_opp_cache[self.season]
        if not p5_season_apg_vs_opp_cache.get(self.season):
            p5_season_apg_vs_opp = self.past5_seasons_avg_apg_vs_opp()
            p5_season_apg_vs_opp_cache[self.season] = p5_season_apg_vs_opp
        else:
            print("Using Cache")
            p5_season_apg_vs_opp = p5_season_apg_vs_opp_cache[self.season]
        if not p5_season_rpg_vs_opp_cache.get(self.season):
            p5_season_rpg_vs_opp = self.past5_seasons_avg_rpg_vs_opp()
            p5_season_rpg_vs_opp_cache[self.season] = p5_season_rpg_vs_opp
        else:
            print("Using Cache")
            p5_season_rpg_vs_opp = p5_season_rpg_vs_opp_cache[self.season]
        if not season_ppg_vs_opp_cache.get(self.season):
            season_ppg_vs_opp = self.season_avg_ppg_vs_opp()
            season_ppg_vs_opp_cache[self.season] = season_ppg_vs_opp
        else:
            print("Using Cache")
            season_ppg_vs_opp = season_ppg_vs_opp_cache[self.season]
        if not season_apg_vs_opp_cache.get(self.season):
            season_apg_vs_opp = self.season_avg_apg_vs_opp()
            season_apg_vs_opp_cache[self.season] = season_apg_vs_opp
        else:
            print("Using Cache")
            season_apg_vs_opp = season_apg_vs_opp_cache[self.season]
        if not season_rpg_vs_opp_cache.get(self.season):
            season_rpg_vs_opp = self.season_avg_rpg_vs_opp()
            season_rpg_vs_opp_cache[self.season] = season_rpg_vs_opp
        else:
            print("Using Cache")
            season_rpg_vs_opp = season_rpg_vs_opp_cache[self.season]
        
        return {
            "P5 Season PPG vs OPP": float(p5_season_ppg_vs_opp),
            "P5 Season APG vs OPP": float(p5_season_apg_vs_opp),
            "P5 Season RPG vs OPP": float(p5_season_rpg_vs_opp),
            "Season PPG vs OPP": float(season_ppg_vs_opp),
            "Season APG vs OPP": float(season_apg_vs_opp),
            "Season RPG vs OPP": float(season_rpg_vs_opp),
        }

    def get_predicting_factors_only_non_opp_data(self):
        def_ranking_cache, index = load_cache(self.player_name, "def_ranking_cache")
        season_ppg_cache, _ = load_cache(self.player_name, "season_ppg_cache")
        season_rpg_cache, _ = load_cache(self.player_name, "season_rpg_cache")
        season_apg_cache, _ = load_cache(self.player_name, "season_apg_cache")
        p5_season_ppg_cache, _ = load_cache(self.player_name, "p5_season_ppg_cache")
        p5_season_apg_cache, _ = load_cache(self.player_name, "p5_season_apg_cache")
        p5_season_rpg_cache, _ = load_cache(self.player_name, "p5_season_rpg_cache")
        

        if not def_ranking_cache.get((self.opp_team_abbrv, self.season)):
            def_ranking = self.get_opp_defensive_ranking()
            def_ranking_cache[(self.opp_team_abbrv, self.season)] = def_ranking
        else:
            print("Using Cache")
            def_ranking = def_ranking_cache[(self.opp_team_abbrv, self.season)]
        if not season_ppg_cache.get(self.season):
            season_ppg = self.season_avg_ppg()
            season_ppg_cache[self.season] = season_ppg
        else:
            print("Using Cache")
            season_ppg = season_ppg_cache[self.season]
        if not season_apg_cache.get(self.season):
            season_apg = self.season_avg_apg()
            season_apg_cache[self.season] = season_apg
        else:
            print("Using Cache")
            season_apg = season_apg_cache[self.season]
        if not season_rpg_cache.get(self.season):
            season_rpg = self.season_avg_rpg()
            season_rpg_cache[self.season] = season_rpg
        else:
            print("Using Cache")
            season_rpg = season_rpg_cache[self.season]
        if not p5_season_ppg_cache.get(self.season):
            p5_season_ppg = self.past5_seasons_avg_ppg()
            p5_season_ppg_cache[self.season] = p5_season_ppg
        else:
            print("Using Cache")
            p5_season_ppg = p5_season_ppg_cache[self.season]
        if not p5_season_apg_cache.get(self.season):
            p5_season_apg = self.past5_seasons_avg_apg()
            p5_season_apg_cache[self.season] = p5_season_apg
        else:
            print("Using Cache")
            p5_season_apg = p5_season_apg_cache[self.season]
        if not p5_season_rpg_cache.get(self.season):
            p5_season_rpg = self.past5_seasons_avg_rpg()
            p5_season_rpg_cache[self.season] = p5_season_rpg
        else:
            print("Using Cache")
            p5_season_rpg = p5_season_rpg_cache[self.season]
        
        return {
            "Opponent Def. Ranking": float(def_ranking),
            "Season PPG": float(season_ppg),
            "Season APG": float(season_apg),
            "Season RPG": float(season_rpg),
            "P5 Season PPG": float(p5_season_ppg),
            "P5 Season APG": float(p5_season_apg),
            "P5 Season RPG": float(p5_season_rpg),
        }
