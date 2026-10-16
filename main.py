import threading
import time
import tkinter as tk

from gui.topbanner import EsportsTopBanner
from lolapi.events.getlive import get_live_games
from lolapi.matchdetails.getwindow import get_window, GameWindow, TeamFrame
from utils import parseTimestamp, now, getTeamNames

BASE_URL = "https://esports-api.lolesports.com/persisted/gw"
API_KEY = "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"


def liveGameData():
    live = get_live_games(api_key=API_KEY)
    current_event = None
    for event in filter(lambda event: event.league.slug == "worlds", live.data.schedule.events):
        current_event = event
    # current_event = find_live_match(live, "Karmine Corp", "Cloud9 Kia")
    if current_event:
        teams = getTeamNames(current_event)
        # pprint(teams)
        active_game = next(
            (game for game in current_event.match.games if game.state == "inProgress"),
            None,
        )
        if active_game:
            showGameData(active_game.id, teams)
        else:
            print(f"No game ID found ({' vs '.join(teams.values())})")



def showGameData(game_id, teams):
    root = tk.Tk()
    root.title("LoL Esports")
    root.configure(bg="#101722")

    banner = EsportsTopBanner(root)
    banner.pack(fill="x", padx=12, pady=12)

    blue_score = 0
    red_score = 2
    game_number = 3
    best_of = 5

    def fetch_and_update():
        """Fetch off the Tk thread; apply results on the Tk thread."""
        try:
            current_time = now()
            window = get_window(game_id, starting_time=current_time)
            first_window = get_window(game_id)

            if window and first_window:
                root.after(
                    0,
                    lambda: banner.update_stats(
                        window,
                        first_window,
                        teams,
                        blue_score=blue_score,
                        red_score=red_score,
                        game_number=game_number,
                        best_of=best_of,
                    ),
                )
            else:
                print(f"No game frames available for {game_id}")
        except Exception as exc:
            print(f"Could not refresh game {game_id}: {exc}")

    def refresh():
        threading.Thread(target=fetch_and_update, daemon=True).start()

        # Align the next refresh with the next wall-clock multiple of 10 seconds.
        delay_ms = 10_000 - (int(time.time()) % 10) * 1_000
        root.after(delay_ms, refresh)

    refresh()
    root.mainloop()


def formatTeamStats(window: GameWindow, first_window: GameWindow, teams: dict[str, str]) -> str:
    if not window.frames or not first_window.frames:
        return f"No game frames available. ({' vs '.join(teams.values())})"

    frame = window.frames[-1]
    first_frame = first_window.frames[0]
    blue = frame.blueTeam
    blue_team_name = teams[window.gameMetadata.blueTeamMetadata.esportsTeamId]
    red = frame.redTeam
    red_team_name = teams[window.gameMetadata.redTeamMetadata.esportsTeamId]

    def dragons(team: TeamFrame) -> str:
        return ", ".join(team.dragons) if team.dragons else "—"

    elapsed = parseTimestamp(frame.rfc460Timestamp) - parseTimestamp(first_frame.rfc460Timestamp)

    total_seconds = int(elapsed.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)

    return (
        f"Game time: {minutes}:{seconds:02}\n"
        f"             {blue_team_name:^30} {red_team_name:^30}\n"
        f"Inhibitors   {blue.inhibitors:^30} {red.inhibitors:^30}\n"
        f"Towers       {blue.towers:^30} {red.towers:^30}\n"
        f"Barons       {blue.barons:^30} {red.barons:^30}\n"
        f"Kills        {blue.totalKills:^30} {red.totalKills:^30}\n"
        f"Team gold    {blue.totalGold:^30} {red.totalGold:^30}\n"
        f"Dragons      {dragons(blue):^30} {dragons(red):^30}"
    )


def main():
    # showGameData("116299649500204437", {"111692118851466302": "Cloud9 Kia", "98767991877340524": "Karmine Corp"})
    liveGameData()


if __name__ == '__main__':
    main()
