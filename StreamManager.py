import os
from obswebsocket import obsws, requests
from pathlib import Path
from paths import image_path, hero_icon_path

HOST = "localhost"
PORT = 4455
PASSWORD = ""

maps = ["Map1", "Map2", "Map3", "Map4", "Map5"]
# Map names dictionary
map_names = {
    "0000.png": "Reset",
    "0001.png": "Lijang",
    "0002.png": "Oasis",
    "0003.png": "Busan",
    "0004.png": "Dorado",
    "0005.png": "Numbani",
    "0006.png": "Havana",
    "0007.png": "Rialto",
    "0008.png": "Circuit",
    "0009.png": "Midtown",
    "0010.png": "Paraiso",
    "0011.png": "Blizz",
    "0012.png": "New Queen Street",
    "0013.png": "Colosseo",
    "0014.png": "Esperanca",
    "0015.png": "Aatlis",
    "0016.png": "NewJunkCity",
    "0017.png": "Suravasa",
}



# Track map winners per map
map_winners = {i: None for i in range(1, len(maps)+1)}

# Total map wins
elysium_map_wins = 0
opponent_map_wins = 0

# Scores (integer keys)
scores = {
    "Elysium": {i+1: 0 for i in range(5)},
    "Opponent": {i+1: 0 for i in range(5)},
}

# Bans per map/team
bans = {map_idx: {"Elysium": set(), "Opponent": set()} for map_idx in range(1, len(maps)+1)}


def connect_ws():
    ws = obsws(HOST, PORT, PASSWORD)
    ws.connect()
    return ws


def set_map(map_index, map_file):
    ws = connect_ws()
    try:
        ws.call(requests.SetInputSettings(
            inputName=maps[map_index - 1],
            inputSettings={"file": os.path.join(image_path, map_file)}
        ))
    finally:
        ws.disconnect()


def update_match_points():
    """Recalculate total map wins for each team and update OBS sources."""
    global elysium_map_wins, opponent_map_wins
    elysium_map_wins = sum(1 for w in map_winners.values() if w == "Elysium")
    opponent_map_wins = sum(1 for w in map_winners.values() if w == "Opponent")

    ws = connect_ws()
    try:
        ws.call(requests.SetInputSettings(
            inputName="Score(home)",
            inputSettings={"text": str(elysium_map_wins)}
        ))
        ws.call(requests.SetInputSettings(
            inputName="Score(Opponent)",
            inputSettings={"text": str(opponent_map_wins)}
        ))
    finally:
        ws.disconnect()


def toggle_map_win(team, map_index):
    """
    Toggle the map win for a given team on a specific map.
    Only one team can have a win per map.
    """
    current_winner = map_winners[map_index]

    if current_winner == team:
        # Undo this team's win
        map_winners[map_index] = None
    else:
        # Set this team as winner
        map_winners[map_index] = team

    # Update total wins and OBS sources
    update_match_points()


def reset():
    """Reset maps, scores, map wins, and bans."""
    global elysium_map_wins, opponent_map_wins
    ws = connect_ws()
    try:
        # Reset map images
        for i in range(5):
            ws.call(requests.SetInputSettings(
                inputName=maps[i],
                inputSettings={"file": os.path.join(image_path, "0000.png")}
            ))

        # Reset scores
        for team in scores:
            for m in scores[team]:
                scores[team][m] = 0
                ws.call(requests.SetInputSettings(
                    inputName=f"{maps[m-1]}_score",
                    inputSettings={"text": f"{scores['Elysium'][m]} : {scores['Opponent'][m]}"}
                ))

        # Reset map winners
        for m in map_winners:
            map_winners[m] = None
        elysium_map_wins = 0
        opponent_map_wins = 0
        ws.call(requests.SetInputSettings(
            inputName="Score(home)",
            inputSettings={"text": str(elysium_map_wins)}
        ))
        ws.call(requests.SetInputSettings(
            inputName="Score(Opponent)",
            inputSettings={"text": str(opponent_map_wins)}
        ))

        # Clear bans only for maps that have ban sources (maps 2-5)
        for m in range(2, 6):
            for team in bans[m]:
                bans[m][team].clear()
                placeholder = hero_icon_path / "Icon-tbd.png"
                if placeholder.exists():
                    ws.call(requests.SetInputSettings(
                        inputName=f"{team}_{m}",
                        inputSettings={"file": str(placeholder)}
                    ))

        item_id = "Map1_score"

        ws.call(requests.SetSceneItemEnabled(
        sceneName="Between",
        sceneItemId=item_id,
        sceneItemEnabled=False
    ))


    
    finally:
        ws.disconnect()


def increment_score(map_index, team):
    """Increment score for a team on a specific map."""
    ws = connect_ws()
    try:
        scores[team][map_index] += 1
        score_text = f"{scores['Elysium'][map_index]} : {scores['Opponent'][map_index]}"
        ws.call(requests.SetInputSettings(
            inputName=f"{maps[map_index-1]}_score",
            inputSettings={"text": score_text}
        ))
    finally:
        ws.disconnect()


def ban_hero(role, hero, map_index, team):
    """Ban a hero by showing its icon on OBS"""
    icon_path = hero_icon_path / role / f"Icon-{hero}.png"
    if not icon_path.exists():
        print(f"Hero icon not found: {icon_path}")
        return

    ws = connect_ws()
    try:
        ws.call(requests.SetInputSettings(
            inputName=f"{team}_{map_index}",
            inputSettings={"file": str(icon_path)}
        ))
        bans[map_index][team].add(hero)
    finally:
        ws.disconnect()


def unban_hero(hero, map_index, team):
    """Unban a hero, replacing with placeholder icon"""
    placeholder = hero_icon_path / "Icon-tbd.png"
    if not placeholder.exists():
        print(f"Placeholder icon not found: {placeholder}")
        return

    ws = connect_ws()
    try:
        ws.call(requests.SetInputSettings(
            inputName=f"{team}_{map_index}",
            inputSettings={"file": str(placeholder)}
        ))
        bans[map_index][team].discard(hero)
    finally:
        ws.disconnect()


