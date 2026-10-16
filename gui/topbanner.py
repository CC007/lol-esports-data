from pathlib import Path
import tkinter as tk

from PIL import Image, ImageTk

from utils import parseTimestamp

DRAGON_ICON_FILES = {
    "chemtech": "Chemtech_Dragon.webp",
    "cloud": "Cloud_Dragon.webp",
    "hextech": "Hextech_Dragon.webp",
    "infernal": "Infernal_Dragon.webp",
    "mountain": "Mountain_Dragon.webp",
    "ocean": "Ocean_Dragon.webp",
}


class EsportsTopBanner(tk.Frame):
    BG = "#07131c"
    TOP = "#10232e"
    STRIP = "#0b1922"
    BLUE = "#20d9e8"
    RED = "#ff4665"
    TEXT = "#f5f7fa"
    MUTED = "#89a0ad"
    GOLD = "#f6d66b"

    def __init__(self, master, height=140):
        super().__init__(master, bg=self.BG)

        self.height = height
        self._stats = None
        self.dragon_icons = {}

        self.canvas = tk.Canvas(
            self,
            height=height,
            bg=self.BG,
            highlightthickness=0,
        )
        self.canvas.pack(fill="x", expand=True)
        self.canvas.bind("<Configure>", self._draw)

        self._load_dragon_icons()

    def _load_dragon_icons(self):
        """Load local WebP dragon icons from the icons folder beside this file."""
        icon_dir = Path(__file__).resolve().parent.parent / "icons"

        for name, filename in DRAGON_ICON_FILES.items():
            path = icon_dir / filename
            try:
                image = Image.open(path).convert("RGBA")
                image.thumbnail((18, 18))
                self.dragon_icons[name] = ImageTk.PhotoImage(image)
            except OSError as exc:
                print(f"Could not load dragon icon {path}: {exc}")

    def update_stats(
            self,
            window,
            first_window,
            teams: dict[str, str],
            *,
            blue_score=0,
            red_score=0,
            game_number=1,
            best_of=3,
    ):
        """Update game data and series scores."""
        self._stats = (
            window,
            first_window,
            teams,
            blue_score,
            red_score,
            game_number,
            best_of,
        )
        self._draw()

    def _draw(self, _event=None):
        canvas = self.canvas
        canvas.delete("all")

        width = canvas.winfo_width()
        if width < 100:
            return

        canvas.create_rectangle(
            0, 0, width, self.height,
            fill=self.BG,
            outline="",
        )

        if self._stats is None:
            self._draw_message(width, "Waiting for live game data")
            return

        (
            window,
            first_window,
            teams,
            blue_score,
            red_score,
            game_number,
            best_of,
        ) = self._stats

        if not window.frames or not first_window.frames:
            self._draw_message(width, "No game frames available")
            return

        frame = window.frames[-1]
        first_frame = first_window.frames[0]
        blue = frame.blueTeam
        red = frame.redTeam

        metadata = window.gameMetadata
        blue_id = metadata.blueTeamMetadata.esportsTeamId
        red_id = metadata.redTeamMetadata.esportsTeamId

        blue_name = teams.get(blue_id, blue_id)
        red_name = teams.get(red_id, red_id)

        start = parseTimestamp(first_frame.rfc460Timestamp)
        end = parseTimestamp(frame.rfc460Timestamp)
        if start is not None and end is not None:
            total_seconds = max(0, int((end - start).total_seconds()))
        else:
            total_seconds = 0

        game_time = f"{total_seconds // 60:02}:{total_seconds % 60:02}"

        self._draw_scoreboard(
            width=width,
            blue_name=blue_name,
            red_name=red_name,
            blue_score=blue_score,
            red_score=red_score,
            game_time=game_time,
            game_number=game_number,
            best_of=best_of,
        )
        self._draw_stats_strip(width, blue, red)

    def _draw_message(self, width, message):
        self.canvas.create_text(
            width / 2,
            self.height / 2,
            text=message,
            fill=self.MUTED,
            font=("Arial", 12, "bold"),
            )

    def _draw_scoreboard(
            self,
            *,
            width,
            blue_name,
            red_name,
            blue_score,
            red_score,
            game_time,
            game_number,
            best_of,
    ):
        canvas = self.canvas
        top_height = 62
        center = width / 2

        canvas.create_rectangle(
            0, 0, width, top_height,
            fill=self.TOP,
            outline="",
        )
        canvas.create_rectangle(
            0, 0, 4, top_height,
            fill=self.BLUE,
            outline="",
        )
        canvas.create_rectangle(
            width - 4, 0, width, top_height,
            fill=self.RED,
            outline="",
            )

        # Names sit at the outer edges; series scores frame the centered clock.
        canvas.create_text(
            width * 0.13, 22,
            text=str(blue_name).upper(),
            fill=self.TEXT,
            font=("Arial", 14, "bold"),
            width=width * 0.22,
            )
        canvas.create_text(
            width * 0.34, 23,
            text=str(blue_score),
            fill=self.GOLD,
            font=("Arial", 23, "bold"),
            )
        canvas.create_text(
            center, 20,
            text=game_time,
            fill=self.GOLD,
            font=("Arial", 19, "bold"),
        )
        canvas.create_text(
            center, 45,
            text=f"GAME {game_number}  ·  BEST OF {best_of}",
            fill=self.MUTED,
            font=("Arial", 7, "bold"),
        )
        canvas.create_text(
            width * 0.66, 23,
            text=str(red_score),
            fill=self.GOLD,
            font=("Arial", 23, "bold"),
            )
        canvas.create_text(
            width * 0.87, 22,
            text=str(red_name).upper(),
            fill=self.TEXT,
            font=("Arial", 14, "bold"),
            width=width * 0.22,
            )

        # Team-color accents at each outer edge.
        canvas.create_line(4, top_height - 2, width / 2, top_height - 2,
                           fill=self.BLUE, width=2)
        canvas.create_line(width / 2, top_height - 2, width - 4, top_height - 2,
                           fill=self.RED, width=2)

    def _draw_stats_strip(self, width, blue, red):
        canvas = self.canvas
        top = 63
        center_width = min(136, width * 0.24)
        side_width = (width - center_width) / 2

        canvas.create_rectangle(
            0, top, width, self.height,
            fill=self.STRIP,
            outline="",
        )

        canvas.create_line(
            side_width, top + 4, side_width, self.height - 4,
            fill="#29404c",
                        )
        canvas.create_line(
            width - side_width, top + 4, width - side_width, self.height - 4,
            fill="#29404c",
            )

        self._draw_side_stats(
            x1=0,
            x2=side_width,
            y1=top,
            y2=self.height,
            team=blue,
            accent=self.BLUE,
        )
        self._draw_side_stats(
            x1=width - side_width,
            x2=width,
            y1=top,
            y2=self.height,
            team=red,
            accent=self.RED,
        )

        difference = blue.totalGold - red.totalGold
        if difference > 0:
            arrow, color = "◀", self.BLUE
        elif difference < 0:
            arrow, color = "▶", self.RED
        else:
            arrow, color = "•", self.MUTED

        center_x = width / 2
        canvas.create_text(
            center_x, top + 16,
            text="GOLD DIFF",
            fill=self.MUTED,
            font=("Arial", 7, "bold"),
                      )
        canvas.create_text(
            center_x, top + 37,
            text=f"{arrow} {self._format_gold(abs(difference))} {arrow}",
            fill=color,
            font=("Arial", 11, "bold"),
                      )

    def _draw_side_stats(self, *, x1, x2, y1, y2, team, accent):
        canvas = self.canvas
        columns = 3
        cell_width = (x2 - x1) / columns
        row_height = (y2 - y1) / 2

        stats = [
            ("TOWERS", str(team.towers)),
            ("GOLD", self._format_gold(team.totalGold)),
            ("KILLS", str(team.totalKills)),
            ("BARONS", str(team.barons)),
            ("DRAGONS", None),
            ("INHIBITORS", str(team.inhibitors)),
        ]

        for index, (label, value) in enumerate(stats):
            row, col = divmod(index, columns)
            cell_x1 = x1 + col * cell_width
            cell_x2 = cell_x1 + cell_width
            center_x = (cell_x1 + cell_x2) / 2
            cell_y = y1 + row * row_height

            canvas.create_text(
                center_x, cell_y + 9,
                text=label,
                fill=self.MUTED,
                font=("Arial", 6, "bold"),
                          )

            if label == "DRAGONS":
                self._draw_dragon_icons(
                    x1=cell_x1,
                    x2=cell_x2,
                    y=cell_y + 27,
                    dragons=team.dragons,
                )
            else:
                canvas.create_text(
                    center_x, cell_y + 27,
                    text=value,
                    fill=accent if label == "GOLD" else self.TEXT,
                    font=("Arial", 9, "bold"),
                              )

    def _draw_dragon_icons(self, *, x1, x2, y, dragons):
        canvas = self.canvas
        dragons = dragons or []

        if not dragons:
            canvas.create_text(
                (x1 + x2) / 2,
                y,
                text="—",
                fill=self.TEXT,
                font=("Arial", 9, "bold"),
                )
            return

        icon_size = 18
        gap = 3
        shown = dragons[:3]
        total_width = len(shown) * icon_size + (len(shown) - 1) * gap
        x = (x1 + x2 - total_width) / 2

        for dragon in shown:
            dragon_name = str(dragon).lower()
            icon_name = next(
                (name for name in self.dragon_icons if name in dragon_name),
                None,
            )
            icon = self.dragon_icons.get(icon_name) if icon_name else None

            if icon:
                canvas.create_image(
                    x + icon_size / 2,
                    y,
                    image=icon,
                    )
            else:
                canvas.create_text(
                    x + icon_size / 2,
                    y,
                    text=str(dragon)[:3].upper(),
                    fill=self.TEXT,
                    font=("Arial", 7, "bold"),
                    )

            x += icon_size + gap

    @staticmethod
    def _format_gold(gold):
        return f"{gold / 1000:.1f}K"
