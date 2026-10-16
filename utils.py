from datetime import datetime, timezone, timedelta

from lolapi.events.getlive import Event


def parseTimestamp(value: str) -> datetime:
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
