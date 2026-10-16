import json
from dataclasses import dataclass
from typing import Any
import requests


@dataclass
class ParticipantMetadata:
    esportsPlayerId: str
    participantId: int
    summonerName: str
    championId: str
    role: str


@dataclass
class WindowTeamMetadata:
    esportsTeamId: str
    participantMetadata: list[ParticipantMetadata]


@dataclass
class GameMetadata:
    patchVersion: str
    blueTeamMetadata: WindowTeamMetadata
    redTeamMetadata: WindowTeamMetadata


@dataclass
class ParticipantStats:
    participantId: int
    level: int
    kills: int
    deaths: int
    assists: int
    creepScore: int
    totalGold: int
    currentHealth: int
    maxHealth: int


@dataclass
class TeamFrame:
    totalGold: int
    inhibitors: int
    towers: int
    barons: int
    totalKills: int
    dragons: list[str]
    participants: list[ParticipantStats]


@dataclass
class GameFrame:
    rfc460Timestamp: str
    gameState: str
    blueTeam: TeamFrame
    redTeam: TeamFrame


@dataclass
class GameWindow:
    esportsGameId: str
    esportsMatchId: str
    gameMetadata: GameMetadata
    frames: list[GameFrame]


def _team_metadata_from_dict(data: dict[str, Any]) -> WindowTeamMetadata:
    return WindowTeamMetadata(
        esportsTeamId=data["esportsTeamId"],
        participantMetadata=[
            ParticipantMetadata(**participant)
            for participant in data["participantMetadata"]
        ],
    )


def _team_frame_from_dict(data: dict[str, Any]) -> TeamFrame:
    return TeamFrame(
        totalGold=data["totalGold"],
        inhibitors=data["inhibitors"],
        towers=data["towers"],
        barons=data["barons"],
        totalKills=data["totalKills"],
        dragons=data["dragons"],
        participants=[
            ParticipantStats(**participant)
            for participant in data["participants"]
        ],
    )


def game_window_from_dict(data: dict[str, Any]) -> GameWindow:
    metadata = data["gameMetadata"]

    return GameWindow(
        esportsGameId=data["esportsGameId"],
        esportsMatchId=data["esportsMatchId"],
        gameMetadata=GameMetadata(
            patchVersion=metadata["patchVersion"],
            blueTeamMetadata=_team_metadata_from_dict(
                metadata["blueTeamMetadata"]
            ),
            redTeamMetadata=_team_metadata_from_dict(
                metadata["redTeamMetadata"]
            ),
        ),
        frames=[
            GameFrame(
                rfc460Timestamp=frame["rfc460Timestamp"],
                gameState=frame["gameState"],
                blueTeam=_team_frame_from_dict(frame["blueTeam"]),
                redTeam=_team_frame_from_dict(frame["redTeam"]),
            )
            for frame in data["frames"]
        ],
    )


def get_window(
        game_id: str,
        starting_time: str | None = None,
        session: requests.Session | None = None,
) -> GameWindow | None:
    """Fetch a game's live-stats window and parse it into dataclasses."""
    client = session or requests.Session()
    params = ""

    if starting_time:
        params = f"startingTime={starting_time}"

    response = client.get(
        f"https://feed.lolesports.com/livestats/v1/window/{game_id}",
        params=params,
        timeout=20,
    )
    # print(f"Http status: {response.status_code}")
    if response.status_code == 200:
        return game_window_from_dict(response.json())
    if response.status_code == 204:
        return None
    if response.text is not None and response.text != "":
        print(json.dumps(json.loads(response.text), indent=2, ensure_ascii=False))
    response.raise_for_status()