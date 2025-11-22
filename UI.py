import os
import tkinter as tk
from tkinter import ttk
from StreamManager import (
    set_map, reset, maps, Path, scores, increment_score,
    ban_hero, unban_hero, bans,toggle_map_win, map_names, print_info
)

# Directory paths
from paths import image_path, hero_icon_path

# Roles
roles = ["Tank", "Damage", "Support"]

# Dictionary of heroes grouped by role
heroes_by_role = {}
for role in roles:
    role_path = hero_icon_path / role
    if role_path.exists():
        heroes_by_role[role] = [
            f.replace("Icon-", "").replace(".png", "")
            for f in os.listdir(role_path)
            if f.startswith("Icon-") and f.endswith(".png")
        ]
    else:
        heroes_by_role[role] = []



# Only include files that exist in the folder
available_maps = [f for f in os.listdir(image_path) if f.endswith(".png")]

# Build GUI
root = tk.Tk()
root.title("Uniliga Game Manager")

# Notebook (tabs)
notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both", padx=10, pady=10)


def open_ban_window(map_index, team):
    """Popup window to manage bans for a specific team on a map"""
    window = tk.Toplevel(root)
    window.title(f"{team} Bans for {maps[map_index-1]}")
    window.geometry("425x675")

    for role in roles:
        role_frame = tk.LabelFrame(window, text=role, padx=5, pady=5)
        role_frame.pack(fill="x", pady=5)

        r, c = 0, 0
        for char in heroes_by_role.get(role, []):
            # Determine initial button color based on current bans
            is_banned = char in bans[map_index][team]
            btn_bg = "red" if is_banned else "SystemButtonFace"

            btn = tk.Button(role_frame, text=char, width=12, height=2, bg=btn_bg)
            btn.grid(row=r, column=c, padx=2, pady=2)

            # Closure to capture button and hero info
            def make_toggle(b, r, h):
                def toggle():
                    if h in bans[map_index][team]:
                        # Unban
                        unban_hero(h, map_index, team)
                        b.config(bg="SystemButtonFace")
                    else:
                        # Ban
                        ban_hero(r, h, map_index, team)
                        b.config(bg="red")
                return toggle

            btn.config(command=make_toggle(btn, role, char))

            c += 1
            if c >= 4:
                c = 0
                r += 1


# Create a tab for each map
for i, map_name in enumerate(maps, start=1):
    tab = ttk.Frame(notebook)
    notebook.add(tab, text=map_name)

    # --- Map Selection Section ---
    tk.Label(tab, text=f"Choose a new map for {map_name}:").pack(pady=(10, 5))
    btn_frame = tk.Frame(tab)
    btn_frame.pack(padx=10, pady=5)

    cols = 4
    row = 0
    col = 0
    for map_file in available_maps:
        btn_text = map_names.get(map_file, map_file)
        btn = tk.Button(
            btn_frame,
            text=btn_text or map_file,
            command=lambda idx=i, f=map_file: set_map(idx, f),
            width=15,
            height=2
        )
        btn.grid(row=row, column=col, padx=5, pady=5)
        col += 1
        if col >= cols:
            col = 0
            row += 1

    # --- Score Section ---
    score_frame = tk.Frame(tab)
    score_frame.pack(pady=10)

    tk.Label(score_frame, text="Team Scores:").grid(row=0, column=0, columnspan=4)

    team1_label = tk.Label(score_frame, text=f"Elysium: {scores['Elysium'][i]}")
    team1_label.grid(row=1, column=0, padx=5)
    team2_label = tk.Label(score_frame, text=f"Opponent: {scores['Opponent'][i]}")
    team2_label.grid(row=1, column=1, padx=5)

    def make_increment(team, map_index, label):
        return lambda: (
            increment_score(map_index, team),
            label.config(text=f"{team}: {scores[team][map_index]}")
        )

    tk.Button(score_frame, text="Add Point Elysium", command=make_increment("Elysium", i, team1_label)).grid(row=2, column=0, padx=5, pady=5)
    tk.Button(score_frame, text="Add Point Opponent", command=make_increment("Opponent", i, team2_label)).grid(row=2, column=1, padx=5, pady=5)

    # --- Map Win Section ---
    map_win_frame = tk.Frame(tab)
    map_win_frame.pack(pady=10)

    tk.Label(map_win_frame, text="Map Winner:").grid(row=0, column=0, columnspan=4)

    # Variable to track current winner for this map
    winner_var = tk.StringVar(value="")  # "", "Elysium", or "Opponent"

    def make_winner_toggle(team, map_index, var):
        def toggle():
            if var.get() == team:
                # Deselect this team
                var.set("")
                toggle_map_win(team, map_index)  # removes win
            else:
                # Select this team
                print(var.get())
                var.set(team)
                toggle_map_win(team, map_index)
        return toggle

    # Elysium winner button
    elysium_btn = tk.Button(
        map_win_frame,
        text="Elysium Wins",
        width=15,
        command=make_winner_toggle("Elysium", i, winner_var)
    )
    elysium_btn.grid(row=1, column=0, padx=5, pady=5)

    # Opponent winner button
    opponent_btn = tk.Button(
        map_win_frame,
        text="Opponent Wins",
        width=15,
        command=make_winner_toggle("Opponent", i, winner_var)
    )
    opponent_btn.grid(row=1, column=1, padx=5, pady=5)

    # Update button colors automatically based on winner_var
    def update_winner_colors(*args):
        winner = winner_var.get()
        elysium_btn.config(bg="#2dd613" if winner == "Elysium" else "SystemButtonFace")
        opponent_btn.config(bg="#f54242" if winner == "Opponent" else "SystemButtonFace")

    winner_var.trace_add("write", update_winner_colors)

    # Initial color update
    update_winner_colors()

    # --- Ban Section Buttons ---
    tk.Button(tab, text="Elysium Bans", command=lambda idx=i: open_ban_window(idx, "Elysium"), bg="#f0a500").pack(pady=10)
    tk.Button(tab, text="Opponent Bans", command=lambda idx=i: open_ban_window(idx, "Opponent"), bg="#f0a500").pack(pady=10)

# Reset all maps button at bottom
reset_btn = tk.Button(root, text="Reset All Maps", command=reset, bg="#f08080")
reset_btn.pack(pady=10, fill="x", padx=20)
def setup_windows():

    # Move OBS window (requires pywin32)
    try:
        import win32gui
        hwnd_obs = win32gui.FindWindow(None, "OBS 32.0.2 - Profile: Overwatch - Scenes: Overwatch")
        hwnd_ui = win32gui.FindWindow(None, "Uniliga Game Manager")
        width = 300
        win32gui.MoveWindow(hwnd_obs, -1927, 577, 974 + width, 1039, True)
        win32gui.MoveWindow(hwnd_ui, -967 + width, 577, 974 - width, 1039, True)
    except Exception as e:
        print("Could not move OBS:", e)

setup_btn = tk.Button(root, text="Setup Layout", command=setup_windows, bg="#00aaff", fg="white")
setup_btn.pack(pady=10, fill="x", padx=20)

tk.Button(root, text="Print Results", command=print_info, bg="#02f54b", fg="white").pack(pady=10, fill="x", padx=20)



root.mainloop()
