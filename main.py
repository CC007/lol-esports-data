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

def get_game_context(game_id):
    """Return the latest event and game containing game_id, or (None, None)."""
    live = get_live_games(api_key=API_KEY)

    for event in live.data.schedule.events:
        for game in event.match.games:
            if game.id == game_id:
                return event, game

    return None, None

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

    # One scoreboard per event/series, not per individual game.
    scoreboards_by_event = {}

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
    tk.Scale(
        delay_frame,
        from_=30,
        to=120,
        resolution=10,
        orient="horizontal",
        variable=delay_value,
        bg="#101722",
        fg="white",
        troughcolor="#29404c",
        highlightthickness=0,
        length=300,
    ).pack(side="right")

    def open_game(event, game):
        event_id = event.id
        scoreboard = scoreboards_by_event.get(event_id)

        if scoreboard is not None and scoreboard.winfo_exists():
            # Reuse the existing series window and switch it to this game.
            scoreboard.select_game(event, game)
            scoreboard.deiconify()
            scoreboard.lift()
            return

        scoreboard = showGameData(
            event,
            game,
            delay_getter=lambda: int(delay_value.get()),
        )
        scoreboards_by_event[event_id] = scoreboard

        def remove_closed_window():
            # Do not remove a newer window if this callback belongs to an old one.
            if scoreboards_by_event.get(event_id) is scoreboard:
                scoreboards_by_event.pop(event_id, None)

        scoreboard.protocol("WM_DELETE_WINDOW", lambda: (
            remove_closed_window(),
            scoreboard.destroy(),
        ))

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

        if len(games) == 1:
            event, game = games[0]
            open_game(event, game)

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
        # open_game handles both creating and reusing the event's window.
        open_game(event, game)

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


def showGameData(event, game, *, delay_getter):
    scoreboard = tk.Toplevel()
    scoreboard.title("LoL Esports")
    scoreboard.configure(bg="#101722")

    banner = EsportsTopBanner(scoreboard)
    banner.pack(fill="x", padx=12, pady=12)

    state = {
        "game_id": game.id,
        "game_number": game.number,
        "best_of": event.match.strategy.count,
        "blue_score": 0,
        "red_score": 0,
        "blue_name": "Blue team",
        "red_name": "Red team",
        "teams": {},
    }

    def set_game_context(new_event, new_game):
        state["game_id"] = new_game.id
        state["game_number"] = new_game.number
        state["best_of"] = new_event.match.strategy.count

        blue_score, red_score = get_series_scores(new_event, new_game)
        state["blue_score"] = blue_score
        state["red_score"] = red_score

        names_by_id = {team.id: team.name for team in new_event.match.teams}
        state["teams"] = names_by_id
        state["blue_name"] = "Blue team"
        state["red_name"] = "Red team"

        for game_team in new_game.teams:
            side = game_team.side.casefold()
            name = names_by_id.get(game_team.id, game_team.id)

            if side == "blue":
                state["blue_name"] = name
            elif side == "red":
                state["red_name"] = name

    set_game_context(event, game)
    scoreboard.select_game = set_game_context

    def fetch_and_update():
        game_id = state["game_id"]

        try:
            current_event, current_game = get_game_context(game_id)

            if current_event is not None and current_game is not None:
                set_game_context(current_event, current_game)

            if current_game is not None and current_game.state == "inProgress":
                window = get_window(
                    game_id,
                    starting_time=now(delay_seconds=delay_getter()),
                )
                first_window = get_window(game_id)

                if window and window.frames and first_window and first_window.frames:
                    scoreboard.after(
                        0,
                        lambda: (
                            banner.update_stats(
                                window,
                                first_window,
                                state["teams"],
                                blue_score=state["blue_score"],
                                red_score=state["red_score"],
                                game_number=state["game_number"],
                                best_of=state["best_of"],
                            )
                            if scoreboard.winfo_exists()
                            else None
                        ),
                    )
                    return

            scoreboard.after(
                0,
                lambda: (
                    banner.show_series_only(
                        state["blue_name"],
                        state["red_name"],
                        blue_score=state["blue_score"],
                        red_score=state["red_score"],
                        game_number=state["game_number"],
                        best_of=state["best_of"],
                    )
                    if scoreboard.winfo_exists()
                    else None
                ),
            )

        except Exception as exc:
            print(f"Could not refresh game {game_id}: {exc}")

            scoreboard.after(
                0,
                lambda: (
                    banner.show_series_only(
                        state["blue_name"],
                        state["red_name"],
                        blue_score=state["blue_score"],
                        red_score=state["red_score"],
                        game_number=state["game_number"],
                        best_of=state["best_of"],
                    )
                    if scoreboard.winfo_exists()
                    else None
                ),
            )

    def refresh():
        if not scoreboard.winfo_exists():
            return

        threading.Thread(target=fetch_and_update, daemon=True).start()

        # Schedule the next refresh at a wall-clock multiple of 10 seconds.
        delay_ms = (10 - int(time.time()) % 10) * 1_000
        scoreboard.after(delay_ms, refresh)

    refresh()
    return scoreboard


def main():
    root = tk.Tk()
    show_game_picker(root)
    root.mainloop()


if __name__ == "__main__":
    main()
