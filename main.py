import sqlite3
from APIData import APIData
from tqdm import tqdm
from sys import exit

def get_past_5_seasons(season):
    curr_year = season
    seasons = []

    for _ in range(5):
        seasons.append(f"{curr_year - 1}-{str(curr_year)[2:]}")
        curr_year -= 1

    return seasons

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
        sql = f"""SELECT AVG(pts), AVG(reb), AVG(ast) FROM PlayerGames WHERE player = \"{player}\" AND year IN {tuple(self.seasons)} AND opponent = \"{opp}\";"""

        cur = self.conn.cursor()
        cur.execute(sql)
        self.conn.commit()

        result = cur.fetchall()

        if result is not None:
            return [round(x, 1) for x in result[0]]

    def get_season_data_vs_opp(self, player, opp):
        sql = f"""SELECT AVG(pts), AVG(reb), AVG(ast) FROM PlayerGames WHERE player = \"{player}\" AND year = \"{self.seasons[0]}\" AND opponent = \"{opp}\";"""


        print(sql)
        cur = self.conn.cursor()
        cur.execute(sql)
        self.conn.commit()

        result = cur.fetchall()
        if result is not None:
            return [round(x, 1) for x in result[0]]

    def check_player_in_db(self, player):
        sql = f"""SELECT player FROM PlayerGames WHERE player = \"{player}\";"""
        
        cur = self.conn.cursor()
        cur.execute(sql)
        self.conn.commit()

        result = cur.fetchone()

        return result

def main():

    with open("players.txt", "r") as player_fp:
        players = player_fp.read().split("\n")[:-1]
        # errored_players = ['Danuel House Jr.', 'Dennis Smith Jr.', 'Derrick Jones Jr.', 'Gary Trent Jr.', 'Harry Giles III', 'JaMychal Green', 'Jaren Jackson Jr.', 'Kelly Oubre Jr.', 'Kevin Knox II', 'Kevin Porter Jr.', 'Larry Nance Jr.', 'Lonnie Walker IV', 'Marcus Morris Sr.', 'Marvin Bagley III', 'Tim Hardaway Jr.', 'Troy Brown Jr.', 'Wendell Carter Jr.']
        db_man = PlayerDataDBManager(r"./PlayerStoredData.db", 2023)

        # print(db_man.get_season_data_vs_opp("DeMar DeRozan", "GSW"))

        # to_repalce = ['Danuel House', 'Dennis Smith', 'Derrick Jones', 'Gary Trent', 'Harry Giles', 'Ja Mychal Green', 'Jaren Jackson', 'Kelly Oubre', 'Kevin Knox', 'Kevin Porter', 'Larry Nance', 'Lonnie Walker', 'Marcus Morris', 'Marvin Bagley', 'Tim Hardaway', 'Troy Brown', 'Wendell Carter']
        # replaced = ['Danuel House Jr.', 'Dennis Smith Jr.', 'Derrick Jones Jr.', 'Gary Trent Jr.', 'Harry Giles III', 'JaMychal Green', 'Jaren Jackson Jr.', 'Kelly Oubre Jr.', 'Kevin Knox II', 'Kevin Porter Jr.', 'Larry Nance Jr.', 'Lonnie Walker IV', 'Marcus Morris Sr.', 'Marvin Bagley III', 'Tim Hardaway Jr.', 'Troy Brown Jr.', 'Wendell Carter Jr.']
        # new_players = []

        # for p in players:
        #     if p in to_repalce:
        #         new_players.append(replaced[to_repalce.index(p)])
        #     else:
        #         new_players.append(p)

        # with open("players.txt", "w") as fp:
        #     fp.write("\n".join(new_players))


        erred = ['Aaron Nesmith', 'Alec Burks', 'Andre Iguodala', 'Anthony Edwards', 'Ben Simmons', 'Bojan Bogdanovic', 'Bradley Beal', 'Bruno Fernando', 'Caleb Martin', 'Cameron Johnson', 'Cody Martin', 'Cody Zeller', 'Damian Jones', 'Darius Bazley', "De'Andre Hunter", 'Dejounte Murray', 'Dorian Finney-Smith', 'Dwight Howard', 'Frank Kaminsky', 'Garrison Mathews', 'Gary Harris', 'Gary Payton II', 'Goga Bitadze', 'Gorgui Dieng', 'Grant Williams', 'Hamidou Diallo', 'Harrison Barnes', 'Hassan Whiteside', 'Immanuel Quickley', 'Isaiah Joe', 'Ish Smith', 'Jaden McDaniels', 'Jalen McDaniels', 'Jalen Smith', 'Jamal Murray', 'James Johnson', 'Jaxson Hayes', 'Jordan McLaughlin', 'Jordan Poole', 'Josh Jackson', 'Justise Winslow', 'Jusuf Nurkic', 'Kawhi Leonard', 'Keldon Johnson', 'Kendrick Nunn', 'Kenrich Williams', 'Kentavious Caldwell-Pope', 'Kenyon Martin Jr.', 'Khem Birch', 'Kristaps Porzingis', 'Luguentz Dort', 'Luka Doncic', 'Malcolm Brogdon', 'Mikal Bridges', 'Mike Muscala', 'Nicolas Batum', 'Norman Powell', 'Oshae Brissett', 'Otto Porter Jr.', 'Pat Connaughton', 'Patrick Williams', 'RJ Barrett', 'Robert Williams III', 'Seth Curry', 'Shake Milton', 'Spencer Dinwiddie', 'Terence Davis', 'Tyrese Maxey', 'Tyus Jones', 'Yuta Watanabe']

        for player in tqdm(erred):
            
            if db_man.check_player_in_db(player) is not None:
                print("cont.")
                continue

            test_class = APIData(player, 2023)

            db_man.insert_averages_data(test_class.get_past5_season_stats())
            db_man.insert_game_data(test_class.get_formatted_game_logs())
        

        # test_class = APIData("LeBron James", 2023)
        # print(test_class.get_past5_season_stats())

        # for player in tqdm(players):

        #     if len(db_man.check_player_in_db(player)) > 0:
        #         print("Skipping; Found Player :D")
        #         continue

        #     try:
        #         test_class = APIData(player, 2023)

        #         db_man.insert_averages_data(test_class.get_past5_season_stats())
        #         #db_man.insert_game_data(test_class.get_formatted_game_logs())
        #     except Exception as e:
        #         #errored_players.append(player)

        #         if ("Read" in str(e)):
        #             exit(1)


if __name__ == "__main__":
    main()