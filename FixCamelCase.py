def camel_case_split(str):
    words = [[str[0]]]
 
    for c in str[1:]:
        if words[-1][-1].islower() and c.isupper():
            words.append(list(c))
        else:
            words[-1].append(c)
 
    return [''.join(word) for word in words]
     

new_string = ""
with open("players.txt", "r") as players:
    for player in players.readlines():
        player = player.rstrip()
        new_string += " ".join(camel_case_split(player)) + "\n"

with open("players.txt", "w") as players:
    players.write(new_string)
    
