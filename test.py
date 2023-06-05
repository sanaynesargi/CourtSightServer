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
    game_finder = LeagueGameFinder(player_or_team_abbreviation='P', player_id_nullable=player_id, season_nullable=season, season_type_nullable='Regular Season', proxy=proxy)
    games = game_finder.get_data_frames()[0]

    # Get the team ID for the first game the player played in during the season
    try:
        team_id = games.iloc[0]["TEAM_ID"]

        # Get the team nickname for the specified team ID
        team_nickname = [team['nickname'] for team in teams.get_teams() if team['id'] == team_id][0]

        return team_nickname
    except IndexError:
        return None

get_team_nickname("Anthony Davis", "2022-23")