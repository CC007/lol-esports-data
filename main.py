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

    for event in live.data.schedule.events:
        if event.league.slug != "worlds":
            continue

        active_game = next(
            (
                game for game in event.match.games
                if game.state == "inProgress"
            ),
            None,
        )

        teams = getTeamNames(event)

        if active_game is None:
            print(f"No game ID found ({' vs '.join(teams.values())})")
            continue

        # Match each active game's side to the corresponding match team.
        match_teams_by_id = {
            team.id: team for team in event.match.teams
        }
        scores = {"blue": 0, "red": 0}

        for game_team in active_game.teams:
            side = game_team.side.casefold()
            match_team = match_teams_by_id.get(game_team.id)

            if side in scores and match_team is not None:
                scores[side] = match_team.result.gameWins

        showGameData(
            active_game.id,
            teams,
            blue_score=scores["blue"],
            red_score=scores["red"],
            game_number=active_game.number,
            best_of=event.match.strategy.count,
        )
        return

    print("No in-progress Worlds game found")


def showGameData(
        game_id,
        teams,
        *,
        blue_score,
        red_score,
        game_number,
        best_of,
):
    root = tk.Tk()
    root.title("LoL Esports")
    root.configure(bg="#101722")

    banner = EsportsTopBanner(root)
    banner.pack(fill="x", padx=12, pady=12)

    def fetch_and_update():
        """Fetch game windows off the Tk thread; update the banner on it."""
        try:
            current_time = now()
            window = get_window(game_id, starting_time=current_time)
            first_window = get_window(game_id)

            if window and first_window:
                def apply_update():
                    if root.winfo_exists():
                        banner.update_stats(
                            window,
                            first_window,
                            teams,
                            blue_score=blue_score,
                            red_score=red_score,
                            game_number=game_number,
                            best_of=best_of,
                        )

                root.after(0, apply_update)
            else:
                print(f"No game frames available for {game_id}")
        except Exception as exc:
            print(f"Could not refresh game {game_id}: {exc}")

    def refresh():
        if not root.winfo_exists():
            return

        threading.Thread(target=fetch_and_update, daemon=True).start()

        # Schedule the next request at the next wall-clock multiple of 10 seconds.
        delay_ms = (10 - int(time.time()) % 10) * 1_000
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
