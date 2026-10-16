from datetime import datetime, timezone, timedelta
from pprint import pprint

from lolapi.events.getlive import get_live_games, find_live_match, Event, Game, League, Team
from lolapi.matchdetails.getwindow import get_window, GameWindow, TeamFrame

BASE_URL = "https://esports-api.lolesports.com/persisted/gw"
API_KEY = "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def now() -> str:
    current_time = datetime.now(timezone.utc)
    # print(current_time)
    current_time_ten_seconds = current_time - timedelta(seconds=current_time.second % 10) - timedelta(seconds=40)
    # print(current_time_ten_seconds)
    return current_time_ten_seconds.isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")


def getTeamNames(event: Event) -> dict[str, str]:
    return {team.id: team.name for team in event.match.teams}


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
            getGameData(active_game.id, teams)
        else:
            print(f"No game found for ID {active_game.id} ({' vs '.join(teams.values())})")


def getGameData(game_id, teams):
    current_time = now()
    # print(current_time)
    window = get_window(game_id, starting_time=current_time)
    first_window = get_window(game_id)
    if window and first_window:
        print(formatTeamStats(window, first_window, teams))
    else:
        print(f"No game found for ID {game_id} ({' vs '.join(teams.values())})")


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
    elapsed = parse_timestamp(frame.rfc460Timestamp) - parse_timestamp(first_frame.rfc460Timestamp)

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
    # getGameData("116299649500204437")
    liveGameData()


if __name__ == '__main__':
    main()
