from APIData import APIData
from datetime import date
from tqdm import tqdm
from glob import glob
from os import remove


def get_players():
    with open("players.txt", "r") as players:
        return [player.rstrip() for player in players.readlines()]


def get_player_data(player, opponent):
    playerData = APIData(player, 2023)

    playerData.set_opponent(opponent, 2023)

    return playerData.get_predicting_factors()


def format_player_data(data):
    return "|".join(data)

                          
def main():
    players = get_players()
    today_date = date.today()

    today_data = ""

    for fp in glob("./*.txt")[3:-1]:
        remove(fp)

    for player in tqdm(players):
        try:
            playerData = APIData(player, 2023)
            factors = [str(x) for x in playerData.get_predicting_factors_only_non_opp_data().values()]
        except Exception:
            continue
        
        today_data += f"{player}-{format_player_data(factors)}/"

    with open(f"{today_date}Players.txt", "w") as fout:
        fout.write(today_data)


if __name__ == '__main__':
    main()
