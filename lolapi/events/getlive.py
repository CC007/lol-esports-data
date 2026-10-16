from dataclasses import dataclass
from typing import Any, Optional

import requests


@dataclass
class DisplayPriority:
    position: int
    status: str


@dataclass
class League:
    id: str
    slug: str
    name: str
    image: str
    priority: int
    displayPriority: DisplayPriority


@dataclass
class Tournament:
    id: str


@dataclass
class Result:
    outcome: Optional[str]
    gameWins: int


@dataclass
class Record:
    wins: int
    losses: int


@dataclass
class Team:
    id: str
    name: str
    slug: str
    code: str
    image: str
    result: Result
    record: Record


@dataclass
class GameTeam:
    id: str
    side: str


@dataclass
class MediaLocale:
    locale: str
    englishName: str
    translatedName: str


@dataclass
class Vod:
    id: str
    parameter: str
    locale: str
    mediaLocale: MediaLocale
    provider: str
    offset: int
    firstFrameTime: Optional[int]
    startMillis: Optional[int]
    endMillis: Optional[int]


@dataclass
class Game:
    number: int
    id: str
    state: str
    teams: list[GameTeam]
    vods: list[Vod]


@dataclass
class Strategy:
    type: str
    count: int


@dataclass
class Match:
    id: str
    teams: list[Team]
    strategy: Strategy
    games: list[Game]


@dataclass
class Stream:
    parameter: str
    locale: str
    mediaLocale: MediaLocale
    provider: str
    countries: list[str]
    offset: int
    statsStatus: str


@dataclass
class Event:
    id: str
    startTime: str
    state: str
    type: str
    blockName: str
    league: League
    tournament: Tournament
    match: Match
    streams: list[Stream]


@dataclass
class Schedule:
    events: list[Event]


@dataclass
class Data:
    schedule: Schedule


@dataclass
class Response:
    data: Data


def _media_locale_from_dict(data: dict[str, Any]) -> MediaLocale:
    return MediaLocale(
        locale=data["locale"],
        englishName=data["englishName"],
        translatedName=data["translatedName"],
    )


def _event_from_dict(data: dict[str, Any]) -> Event:
    league_data = data["league"]
    league = League(
        id=league_data["id"],
        slug=league_data["slug"],
        name=league_data["name"],
        image=league_data["image"],
        priority=league_data["priority"],
        displayPriority=DisplayPriority(**league_data["displayPriority"]),
    )

    match_data = data["match"]
    match_teams = [
        Team(
            id=team["id"],
            name=team["name"],
            slug=team["slug"],
            code=team["code"],
            image=team["image"],
            result=Result(**team["result"]),
            record=Record(**team["record"]),
        )
        for team in match_data["teams"]
    ]

    games = []
    for game in match_data.get("games", []):
        vods = [
            Vod(
                id=vod["id"],
                parameter=vod["parameter"],
                locale=vod["locale"],
                mediaLocale=_media_locale_from_dict(vod["mediaLocale"]),
                provider=vod["provider"],
                offset=vod["offset"],
                firstFrameTime=vod.get("firstFrameTime"),
                startMillis=vod.get("startMillis"),
                endMillis=vod.get("endMillis"),
            )
            for vod in game.get("vods", [])
        ]

        games.append(
            Game(
                number=game["number"],
                id=game["id"],
                state=game["state"],
                teams=[GameTeam(**team) for team in game.get("teams", [])],
                vods=vods,
            )
        )

    match = Match(
        id=match_data["id"],
        teams=match_teams,
        strategy=Strategy(**match_data["strategy"]),
        games=games,
    )

    streams = [
        Stream(
            parameter=stream["parameter"],
            locale=stream["locale"],
            mediaLocale=_media_locale_from_dict(stream["mediaLocale"]),
            provider=stream["provider"],
            countries=stream.get("countries", []),
            offset=stream["offset"],
            statsStatus=stream["statsStatus"],
        )
        for stream in data.get("streams", [])
    ]

    return Event(
        id=data["id"],
        startTime=data["startTime"],
        state=data["state"],
        type=data["type"],
        blockName=data["blockName"],
        league=league,
        tournament=Tournament(**data["tournament"]),
        match=match,
        streams=streams,
    )


def response_from_dict(payload: dict[str, Any]) -> Response:
    events = (
        payload.get("data", {})
        .get("schedule", {})
        .get("events", [])
    )
    return Response(
        data=Data(
            schedule=Schedule(events=[_event_from_dict(event) for event in events])
        )
    )


def get_live_games(
        api_key: str,
        locale: str = "en-US",
        session: requests.Session | None = None,
) -> Response:
    client = session or requests.Session()

    response = client.get(
        "https://esports-api.lolesports.com/persisted/gw/getLive",
        headers={
            "x-api-key": api_key,
            "Accept": "application/json",
        },
        params={"hl": locale},
        timeout=20,
    )
    # print(f"Http status: {response.status_code}")
    # print(json.dumps(json.loads(response.text), indent=2, ensure_ascii=False))
    response.raise_for_status()
    return response_from_dict(response.json())


def find_live_match(
        live_response: Response,
        team_a: str,
        team_b: str,
) -> Event | None:
    requested = {team_a.casefold(), team_b.casefold()}

    for event in live_response.data.schedule.events:
        names = {team.name.casefold() for team in event.match.teams}
        if requested.issubset(names):
            return event

    return None