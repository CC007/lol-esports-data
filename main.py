import threading
import time
import tkinter as tk
from tkinter import messagebox

from gui.topbanner import EsportsTopBanner
from lolapi.events.getlive import get_live_games
from lolapi.matchdetails.getwindow import get_window
from utils import now, getTeamNames


BASE_URL = "https://esports-api.lolesports.com/persisted/gw"
API_KEY = "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"


def get_in_progress_games():
    """Return (event, game) pairs for all currently in-progress games."""
    live = get_live_games(api_key=API_KEY)

    return [
        (event, game)
        for event in live.data.schedule.events
        for game in event.match.games
        if game.state == "inProgress"
    ]


def get_series_scores(event, game):
    """Return the current series scores from the active game's blue/red sides."""
    teams_by_id = {team.id: team for team in event.match.teams}
    scores = {"blue": 0, "red": 0}

    for game_team in game.teams:
        side = game_team.side.casefold()
        match_team = teams_by_id.get(game_team.id)

        if side in scores and match_team is not None:
            scores[side] = match_team.result.gameWins

    return scores["blue"], scores["red"]


def show_game_picker(root):
    root.title("Select an in-progress game")
    root.configure(bg="#101722")
    root.geometry("620x360")

    tk.Label(
        root,
        text="IN-PROGRESS GAMES",
        bg="#101722",
        fg="white",
        font=("Arial", 16, "bold"),
    ).pack(pady=(14, 8))

    game_list = tk.Listbox(
        root,
        bg="#0b1922",
        fg="white",
        selectbackground="#176b7a",
        font=("Arial", 11),
        height=10,
    )
    game_list.pack(fill="both", expand=True, padx=16)

    # Keep the corresponding event/game objects alongside the displayed rows.
    games = []

    delay_frame = tk.Frame(root, bg="#101722")
    delay_frame.pack(fill="x", padx=16, pady=(10, 0))

    tk.Label(
        delay_frame,
        text="Game-data delay (seconds):",
        bg="#101722",
        fg="white",
    ).pack(side="left")

    delay_value = tk.StringVar(value="40")
    delay_slider = tk.Scale(
        delay_frame,
        from_=0,
        to=120,
        resolution=10,
        orient="horizontal",
        variable=delay_value,
        bg="#101722",
        fg="white",
        troughcolor="#29404c",
        highlightthickness=0,
        length=300,
    )
    delay_slider.pack(side="right")

    def refresh_game_list():
        try:
            updated_games = get_in_progress_games()
        except Exception as exc:
            messagebox.showerror("Live games unavailable", str(exc), parent=root)
            root.after(10_000, refresh_game_list)
            return

        games.clear()
        games.extend(updated_games)
        game_list.delete(0, tk.END)

        for event, game in games:
            team_names = {team.id: team.name for team in event.match.teams}
            sides = {team.id: team.side.casefold() for team in game.teams}

            blue_name = next(
                (
                    team_names[team_id]
                    for team_id, side in sides.items()
                    if side == "blue" and team_id in team_names
                ),
                "Blue team",
            )
            red_name = next(
                (
                    team_names[team_id]
                    for team_id, side in sides.items()
                    if side == "red" and team_id in team_names
                ),
                "Red team",
            )

            game_list.insert(
                tk.END,
                f"{event.league.name} | Game {game.number} | "
                f"{blue_name} vs {red_name}",
            )

        root.after(10_000, refresh_game_list)

    def open_selected_game():
        selection = game_list.curselection()
        if not selection:
            messagebox.showinfo(
                "Select a game",
                "Choose an in-progress game first.",
                parent=root,
            )
            return

        event, game = games[selection[0]]
        blue_score, red_score = get_series_scores(event, game)

        showGameData(
            game.id,
            getTeamNames(event),
            blue_score=blue_score,
            red_score=red_score,
            game_number=game.number,
            best_of=event.match.strategy.count,
            delay_getter=lambda: int(delay_value.get()),
        )

    tk.Button(
        root,
        text="Open scoreboard",
        command=open_selected_game,
        bg="#176b7a",
        fg="white",
        activebackground="#20d9e8",
        font=("Arial", 11, "bold"),
    ).pack(pady=12)

    refresh_game_list()


def showGameData(
        game_id,
        teams,
        *,
        blue_score,
        red_score,
        game_number,
        best_of,
        delay_getter,
):
    scoreboard = tk.Toplevel()
    scoreboard.title("LoL Esports")
    scoreboard.configure(bg="#101722")

    banner = EsportsTopBanner(scoreboard)
    banner.pack(fill="x", padx=12, pady=12)

    def fetch_and_update():
        try:
            window = get_window(
                game_id,
                starting_time=now(delay_seconds=delay_getter()),
            )
            first_window = get_window(game_id)

            if window and first_window:
                def apply_update():
                    if scoreboard.winfo_exists():
                        banner.update_stats(
                            window,
                            first_window,
                            teams,
                            blue_score=blue_score,
                            red_score=red_score,
                            game_number=game_number,
                            best_of=best_of,
                        )

                scoreboard.after(0, apply_update)
            else:
                print(f"No game frames available for {game_id}")
        except Exception as exc:
            print(f"Could not refresh game {game_id}: {exc}")

    def refresh():
        if not scoreboard.winfo_exists():
            return

        threading.Thread(target=fetch_and_update, daemon=True).start()

        # Refresh at the next wall-clock multiple of 10 seconds.
        delay_ms = (10 - int(time.time()) % 10) * 1_000
        scoreboard.after(delay_ms, refresh)

    refresh()


def main():
    root = tk.Tk()
    show_game_picker(root)
    root.mainloop()


if __name__ == "__main__":
    main()
