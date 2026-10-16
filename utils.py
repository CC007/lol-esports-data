from datetime import datetime, timezone, timedelta

from lolapi.events.getlive import Event


def parseTimestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def now(delay_seconds: int = 40) -> str:
    current_time = datetime.now(timezone.utc)
    rounded_time = current_time - timedelta(seconds=current_time.second % 10)
    delayed_time = rounded_time - timedelta(seconds=delay_seconds)

    return delayed_time.isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")


def getTeamNames(event: Event) -> dict[str, str]:
    return {team.id: team.name for team in event.match.teams}
