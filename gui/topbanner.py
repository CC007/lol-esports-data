import tkinter as tk
from tkinter import ttk

from utils import parseTimestamp


class EsportsTopBanner(ttk.Frame):
    BG = "#07131c"
    TOP = "#10232e"
    STRIP = "#0b1922"
    BLUE = "#20d9e8"
    RED = "#ff4665"
    TEXT = "#f5f7fa"
    MUTED = "#89a0ad"
    GOLD = "#f6d66b"

    def __init__(self, master, height=84):
        super().__init__(master)
        self.height = height
        self._stats = None

        self.canvas = tk.Canvas(
            self,
            height=height,
            bg=self.BG,
            highlightthickness=0,
        )
        self.canvas.pack(fill="x", expand=True)
        self.canvas.bind("<Configure>", self._draw)

    def update_stats(
            self,
            window,
            first_window,
            teams,
            *,
            blue_score=0,
            red_score=0,
            game_number=2,
            best_of=5,
    ):
        """Update the banner. Series scores must be supplied separately."""
        self._stats = (
            window, first_window, teams,
            blue_score, red_score, game_number, best_of,
        )
        self._draw()

    def _draw(self, _event=None):
        c = self.canvas
        c.delete("all")

        width = c.winfo_width()
        if width < 100:
            return

        c.create_rectangle(0, 0, width, self.height, fill=self.BG, outline="")
        if not self._stats:
            return

        (
            window, first_window, teams,
            blue_score, red_score, game_number, best_of,
        ) = self._stats

        if not window.frames or not first_window.frames:
            c.create_text(
                width / 2, self.height / 2,
                text="No game frames available",
                fill=self.MUTED,
                font=("Arial", 11, "bold"),
                )
            return

        frame = window.frames[-1]
        first_frame = first_window.frames[0]
        blue, red = frame.blueTeam, frame.redTeam
        metadata = window.gameMetadata

        blue_id = metadata.blueTeamMetadata.esportsTeamId
        red_id = metadata.redTeamMetadata.esportsTeamId
        blue_name = teams.get(blue_id, blue_id)
        red_name = teams.get(red_id, red_id)

        elapsed = parseTimestamp(frame.rfc460Timestamp) - parseTimestamp(
            first_frame.rfc460Timestamp
        )
        seconds = max(0, int(elapsed.total_seconds()))
        game_time = f"{seconds // 60:02}:{seconds % 60:02}"

        top_h = int(self.height * 0.68)
        mid = width / 2

        # Main scoreboard band
        c.create_rectangle(0, 0, width, top_h, fill=self.TOP, outline="")
        c.create_rectangle(0, 0, 4, top_h, fill=self.BLUE, outline="")
        c.create_rectangle(width - 4, 0, width, top_h, fill=self.RED, outline="")

        # Team names
        c.create_text(
            width * 0.16, top_h * 0.43,
            text=str(blue_name).upper(),
            fill=self.TEXT,
            font=("Arial", 14, "bold"),
            width=width * 0.22,
            )
        c.create_text(
            width * 0.84, top_h * 0.43,
            text=str(red_name).upper(),
            fill=self.TEXT,
            font=("Arial", 14, "bold"),
            width=width * 0.22,
            )

        # Series score and game clock
        c.create_text(
            width * 0.38, top_h * 0.40,
            text=str(blue_score),
            fill=self.GOLD,
            font=("Arial", 23, "bold"),
            )
        c.create_text(
            mid, top_h * 0.34,
            text=game_time,
            fill=self.GOLD,
            font=("Arial", 18, "bold"),
                 )
        c.create_text(
            mid, top_h * 0.76,
            text=f"GAME {game_number}  •  BEST OF {best_of}",
            fill=self.MUTED,
            font=("Arial", 7, "bold"),
                 )
        c.create_text(
            width * 0.62, top_h * 0.40,
            text=str(red_score),
            fill=self.GOLD,
            font=("Arial", 23, "bold"),
            )

        # Thin divider and compact stats strip
        c.create_rectangle(0, top_h, width, top_h + 1, fill="#29404c", outline="")
        strip_y = top_h + (self.height - top_h) / 2

        self._stat(c, width * 0.10, strip_y, "TOWERS", blue.towers, red.towers)
        self._stat(c, width * 0.28, strip_y, "GOLD", self._gold(blue), self._gold(red))
        self._stat(c, width * 0.45, strip_y, "KILLS", blue.totalKills, red.totalKills)
        self._stat(c, width * 0.63, strip_y, "GOLD", self._gold(red), self._gold(blue))
        self._stat(c, width * 0.81, strip_y, "TOWERS", red.towers, blue.towers)

        # Dragons are useful, but fit best as a small footer label when space allows.
        if width >= 650:
            c.create_text(
                width / 2, self.height - 4,
                text=f"DRAGONS  {self._dragons(blue)}   •   {self._dragons(red)}",
                fill=self.MUTED,
                font=("Arial", 7),
                )

    def _stat(self, canvas, x, y, label, left_value, right_value):
        canvas.create_text(
            x, y - 6,
            text=label,
            fill=self.MUTED,
            font=("Arial", 6, "bold"),
               )
        canvas.create_text(
            x, y + 4,
            text=f"{left_value}                         {right_value}",
            fill=self.TEXT,
            font=("Arial", 8, "bold"),
               )

    @staticmethod
    def _gold(team):
        return f"{team.totalGold / 1000:.1f}K"

    @staticmethod
    def _dragons(team):
        return ", ".join(team.dragons) if team.dragons else "—"