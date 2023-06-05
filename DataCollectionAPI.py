import sqlite3
from flask import Flask, request, send_from_directory, make_response
from APIData import APIData, get_player_id, get_player_info, get_players_on_team
from datetime import date
from flask_cors import CORS
from copy import deepcopy

from teamAbbrv import TEAMABBRVMAP


def get_past_5_seasons(season):
    curr_year = season
    seasons = []

    for _ in range(5):
        seasons.append(f"{curr_year - 1}-{str(curr_year)[2:]}")
        curr_year -= 1

    return seasons

def getPlayerData(player, opponent):
  try:
    formatted_player = player
    today_date = date.today()

    pulled_data = db_manager.check_player(player, opponent)

    if pulled_data is not None:
      return pulled_data

    with open(f"{today_date}Players.txt", "r") as player_data:
      formatted_data = player_data.read().split("/")
      player_raw_data = [x for x in formatted_data if formatted_player in x]

      if len(player_raw_data) == 0:
        print(player)
        return None
        try:
          opp_data_collector = APIData(formatted_player, 2023)
          opp_data_collector.set_opponent(opponent, 2023)
          opp_values = list(opp_data_collector.get_predicting_factors().values())


          db_data_str = "|".join(map(str, deepcopy(opp_values)))

          db_data_values = [player, opponent, db_data_str]
          db_manager.insert_data(db_data_values)
    
          return opp_values
        except Exception as e:
    
          return None

      player_raw_data = player_raw_data[0]
      player_formatted_data = [float(x) for x in player_raw_data.split("-")[-1].split("|")]


    p5 = player_db_manager.get_past_5_season_data_vs_opp(formatted_player, TEAMABBRVMAP[opponent])
    curr = player_db_manager.get_season_data_vs_opp(formatted_player, TEAMABBRVMAP[opponent])

    if not p5 or not curr:
        return None

    opp_values = p5
    opp_values.extend(curr)

    player_formatted_data.extend(opp_values)

    db_data_str = "|".join(map(str, deepcopy(player_formatted_data)))
    db_data_values = [player, opponent, db_data_str]
    db_manager.insert_data(db_data_values)
    
    return player_formatted_data

  except Exception as e:
    resp = make_response({"error": str(e)})
    resp.headers['Access-Control-Allow-Origin'] = '*'
    
    return resp


class CacheDBMAnager:
    def __init__(self, db_path):
        self.date = date.today()
        self.conn = self.create_connection(db_path)

        self.create_data_table()
        self.create_info_table()

    def create_connection(self, db_file):
        """ create a database connection to the SQLite database
            specified by db_file
        :param db_file: database file
        :return: Connection object or None
        """
        conn = None
        try:
            conn = sqlite3.connect(db_file, check_same_thread=False)
        except Exception as e:
            print(e)

        return conn

    def create_data_table(self):
        sql = f""" CREATE TABLE IF NOT EXISTS \"PlayerDataCaches{self.date}\" (
                player TEXT NOT NULL,
                opponent TEXT NOT NULL,
                data TEXT NOT NULL
        ); """
        cur = self.conn.cursor()
        cur.execute(sql)
        self.conn.commit()

    def create_info_table(self):
        sql = f""" CREATE TABLE IF NOT EXISTS \"PlayerInfoCaches{self.date}\" (
                player TEXT NOT NULL,
                team TEXT NOT NULL,
                abbrv TEXT NOT NULL,
                height TEXT NOT NULL,
                weight TEXT NOT NULL,
                number TEXT NOT NULL,
                position TEXT NOT NULL,
                ts REAL NOT NULL,
                ppg REAL NOT NULL,
                rpg REAL NOT NULL,
                apg REAL NOT NULL
        ); """
        cur = self.conn.cursor()
        cur.execute(sql)
        self.conn.commit()

    def insert_info(self, data):
        sql = f''' INSERT INTO \"PlayerInfoCaches{self.date}\"  (
                player, height, weight, number, position, team, abbrv, ts, ppg, rpg, apg
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?);
        '''

        cur = self.conn.cursor()
        cur.execute(sql, tuple(data))
        self.conn.commit()
        return cur.lastrowid 

    def check_info(self, player):
      sql = f"""SELECT * FROM \"PlayerInfoCaches{self.date}\" WHERE player = \"{player}\";"""

      cur = self.conn.cursor()
      cur.execute(sql)
      self.conn.commit()

      result = cur.fetchone()

      if result is not None:
        return result


    def insert_data(self, data):
        sql = f''' INSERT INTO \"PlayerDataCaches{self.date}\"  (
                player, opponent, data
            ) VALUES(?,?,?);
        '''

        cur = self.conn.cursor()
        cur.execute(sql, tuple(data))
        self.conn.commit()
        return cur.lastrowid

    def check_player(self, player, opponent):
        sql = f"""SELECT data FROM \"PlayerDataCaches{self.date}\" WHERE player = \"{player}\" AND opponent = \"{opponent}\";"""

        cur = self.conn.cursor()
        cur.execute(sql)
        self.conn.commit()

        result = cur.fetchone()
        if result is not None:
          result_formatted = [float(x) for x in result[0].split("|")]
          return result_formatted

class PlayerDataDBManager:
    def __init__(self, db_path, season_num):
        self.conn = self.create_connection(db_path)
        self.seasons = get_past_5_seasons(season_num)

        self.create_averages_table()
        self.create_game_table()


    def create_connection(self, db_file):
        """ create a database connection to the SQLite database
            specified by db_file
        :param db_file: database file
        :return: Connection object or None
        """
        conn = None
        try:
            conn = sqlite3.connect(db_file, check_same_thread=False)
        except Exception as e:
            print(e)

        return conn

    def create_averages_table(self):
        sql = f""" CREATE TABLE IF NOT EXISTS PlayerAverages (
                player TEXT NOT NULL,
                year TEXT NOT NULL,
                ppg REAL NOT NULL,
                rpg REAL NOT NULL,
                apg REAL NOT NULL,
                gp REAL NOT NULL
        ); """
        cur = self.conn.cursor()
        cur.execute(sql)
        self.conn.commit()

    def create_game_table(self):
        sql = f""" CREATE TABLE IF NOT EXISTS PlayerGames (
                player TEXT NOT NULL,
                year TEXT NOT NULL,
                opponent TEXT NOT NULL,
                pts REAL NOT NULL,
                reb REAL NOT NULL,
                ast REAL NOT NULL
        ); """
        cur = self.conn.cursor()
        cur.execute(sql)
        self.conn.commit()

    def insert_averages_data(self, data):
        sql = f''' INSERT INTO PlayerAverages (
                player, year, ppg, rpg, apg, gp
            ) VALUES(?,?,?,?,?,?);
        '''
        
        for chunk in data:
            cur = self.conn.cursor()
            cur.execute(sql, chunk)
            self.conn.commit()

    def insert_game_data(self, data):
        sql = f''' INSERT INTO PlayerGames (
                player, year, opponent, pts, reb, ast
            ) VALUES(?,?,?,?,?,?);
        '''
        
        for chunk in data:
            cur = self.conn.cursor()
            cur.execute(sql, chunk)
            self.conn.commit()

    def get_past_5_season_data_vs_opp(self, player, opp):
        sql = f"""SELECT AVG(pts), AVG(ast), AVG(reb) FROM PlayerGames WHERE player = \"{player}\" AND year IN {tuple(self.seasons)} AND opponent = \"{opp}\";"""

        cur = self.conn.cursor()
        cur.execute(sql)
        self.conn.commit()

        result = cur.fetchall()

        if None not in result[0]:
            return [round(x, 1) for x in result[0]]

    def get_season_data_vs_opp(self, player, opp):
        sql = f"""SELECT AVG(pts), AVG(ast), AVG(reb) FROM PlayerGames WHERE player = \"{player}\" AND year = \"{self.seasons[0]}\" AND opponent = \"{opp}\";"""

        cur = self.conn.cursor()
        cur.execute(sql)
        self.conn.commit()

        result = cur.fetchall()


        if None not in result[0]:
            return [round(x, 1) for x in result[0]]

    def check_player_in_db(self, player):
        sql = f"""SELECT player FROM PlayerAverages WHERE player = \"{player}\";"""
        
        cur = self.conn.cursor()
        cur.execute(sql)
        self.conn.commit()

        result = cur.fetchall()


app = Flask(__name__, static_folder="./static")
db_manager = CacheDBMAnager(r"./PlayerDataCaches.db")
player_db_manager = PlayerDataDBManager(r"./PlayerStoredData.db", 2023)

CORS(app)


@app.route('/')
def index():
    return 'Reached Server!'


@app.route('/<path:filename>')  
def send_file(filename):  
    resp = make_response(send_from_directory(app.static_folder, filename))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

  
@app.get("/getHeadshotURL")
def getHeadShotURL():
  player = request.args.get("player")

  if not player:
    resp = make_response({"error": "Invalid Player"})
    resp.headers['Access-Control-Allow-Origin'] = '*'

    return resp

  try:
    formatted_player = " ".join(player.split("|"))[:-1]
    id = get_player_id(formatted_player)

    resp = make_response({"data": f"https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/{id}.png"})
    resp.headers['Access-Control-Allow-Origin'] = '*'

    return resp
  except Exception as e:
    resp = make_response({"error": str(e)})
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.get("/getPlayerInfo")
def getPlayerInfo():
  player = request.args.get("player")

  if not player:
    resp = make_response({"error": "Invalid Player"})
    resp.headers['Access-Control-Allow-Origin'] = '*'
    
    return resp


  try:
    formatted_player = player.split("|")
    formatted_player = formatted_player[0] + " " + formatted_player[1]
 
    print(formatted_player)
 
    playerDataCollector = APIData(formatted_player, 2023)
    today_date = date.today()
    
    db_info = db_manager.check_info(formatted_player)

    if db_info:
      data = {
        "#": db_info[1],
        "POS": db_info[2],
        "Team": db_info[3],
        "Abbrv": db_info[4],
        "Height": db_info[5],
        "Weight": db_info[6],
        "TS": db_info[7],
        "PPG": db_info[8],
        "APG": db_info[9],
        "RPG": db_info[10],
      }

      resp = make_response({"data": data})
      resp.headers['Access-Control-Allow-Origin'] = '*'

      return resp
      

    with open(f"{today_date}Players.txt", "r") as player_data:
      formatted_data = player_data.read().split("/")
      player_raw_data = [x for x in formatted_data if formatted_player in x]

      if len(player_raw_data) == 0:
        ppg = playerDataCollector.season_avg_ppg()
        apg = playerDataCollector.season_avg_apg()
        rpg = playerDataCollector.season_avg_rpg()
      else:
        player_raw_data = player_raw_data[0]
        player_formatted_data = [float(x) for x in player_raw_data.split("-")[-1].split("|")]
        ppg = player_formatted_data[1]
        apg = player_formatted_data[2]
        rpg = player_formatted_data[3]

    intrinsic_data = get_player_info(formatted_player)

    intrinsic_data["PPG"] = ppg
    intrinsic_data["APG"] = apg
    intrinsic_data["RPG"] = rpg


    db_data = list(intrinsic_data.values())
    db_data.insert(0, formatted_player)
    db_manager.insert_info(tuple(db_data))

    resp = make_response({"data": intrinsic_data})
    resp.headers['Access-Control-Allow-Origin'] = '*'
    
    return resp
  except Exception as e:
    raise e
    resp = make_response({"error": str(e)})
    resp.headers['Access-Control-Allow-Origin'] = '*'
    
    return resp


@app.get("/playersOnTeam")
def getPlayersOnTeam():
  team = request.args.get("team")
  opponent = request.args.get("opponent")


  if not team:
    resp = make_response({"error": "Invalid Team"})
    resp.headers['Access-Control-Allow-Origin'] = '*'
    
    return resp
  if not opponent:
    resp = make_response({"error": "Invalid Opponent"})
    resp.headers['Access-Control-Allow-Origin'] = '*'
    
    return resp
  if opponent == team:
    resp = make_response({"error": "Team and Opponent Cannot be Equal"})
    resp.headers['Access-Control-Allow-Origin'] = '*'
    
    return resp
  
  try:
    players = set(get_players_on_team(team))

    with open("players.txt", "r") as players_fp:
      m_players = set(players_fp.read().split("\n")[:-1])

  
    team_players = m_players.intersection(players)
    return_data = []

    for player in team_players:
      data = getPlayerData(player, opponent)

      if data is not None:
        return_data.append([player, data])

    resp = make_response({"data": return_data})
    resp.headers['Access-Control-Allow-Origin'] = '*'
    
    return resp
  except Exception as e:
    print(e)
    resp = make_response({"error": str(e)})
    resp.headers['Access-Control-Allow-Origin'] = '*'
    
    return resp


@app.get('/getPlayerData')
def getData():
  player = request.args.get('player')
  opponent = request.args.get('opponent')
 
  if not player:
    return {"error": "Player not found"}
  elif not opponent:
    return {"error": "Opponent not found"}
  
  try:
    formatted_player = player.split("|")
    formatted_player = formatted_player[0] + " " + formatted_player[1]
    today_date = date.today()

    pulled_data = db_manager.check_player(player, opponent)

    if pulled_data is not None:
      resp = make_response({"data": pulled_data})
      resp.headers['Access-Control-Allow-Origin'] = '*'

      return resp

    with open(f"{today_date}Players.txt", "r") as player_data:
      formatted_data = player_data.read().split("/")
      player_raw_data = [x for x in formatted_data if formatted_player in x]

      if len(player_raw_data) == 0:
        try:
          opp_data_collector = APIData(formatted_player, 2023)
          opp_data_collector.set_opponent(opponent, 2023)
          opp_values = list(opp_data_collector.get_predicting_factors().values())

          resp = make_response({"data": opp_values})
          resp.headers['Access-Control-Allow-Origin'] = '*'

          db_data_str = "|".join(map(str, deepcopy(opp_values)))

          db_data_values = [player, opponent, db_data_str]
          db_manager.insert_data(db_data_values)
    
          return resp
        except Exception as e:
          print(e)
          resp = make_response({"error": str(e)})
          resp.headers['Access-Control-Allow-Origin'] = '*'
    
          return resp

      player_raw_data = player_raw_data[0]
      player_formatted_data = [float(x) for x in player_raw_data.split("-")[-1].split("|")]

    opp_data_collector = APIData(formatted_player, 2023)
    opp_data_collector.set_opponent(opponent, 2023)
    # opp_values = 

    p5 = player_db_manager.get_past_5_season_data_vs_opp(formatted_player, TEAMABBRVMAP[opponent])
    curr = player_db_manager.get_season_data_vs_opp(formatted_player, TEAMABBRVMAP[opponent])

    if not p5 or not curr:
        resp = make_response({"error": "No Games Played"})
        resp.headers['Access-Control-Allow-Origin'] = '*'
    
        return resp

    opp_values = p5
    opp_values.extend(curr)

    player_formatted_data.extend(opp_values)

    db_data_str = "|".join(map(str, deepcopy(player_formatted_data)))
    db_data_values = [player, opponent, db_data_str]
    db_manager.insert_data(db_data_values)

    
    player_formatted_data[0] = 30 - player_formatted_data[0]

    resp = make_response({"data": player_formatted_data})
    resp.headers['Access-Control-Allow-Origin'] = '*'
    
    return resp

  except Exception as e:
    resp = make_response({"error": str(e)})
    resp.headers['Access-Control-Allow-Origin'] = '*'
    
    return resp
  
  
app.run(host="127.0.0.1", port="8000", debug=True)
