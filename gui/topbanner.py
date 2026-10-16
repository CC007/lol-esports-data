import tkinter as tk
from tkinter import ttk

from utils import parseTimestamp


class EsportsTopBanner(ttk.Frame):
    BG = "#101722"
    PANEL = "#182433"
    BLUE = "#39a9ff"
    RED = "#ff5364"
    TEXT = "#f2f5f8"
    MUTED = "#9aa9b8"
    GOLD = "#f4c95d"

    def __init__(self, master, height=190):
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

        # Redraw on resize instead of clearing the canvas.
        self.canvas.bind("<Configure>", self._on_resize)

    def update_stats(self, window, first_window, teams):
        """Save the latest data, then draw it when the canvas has a real size."""
        self._stats = (window, first_window, teams)
        self._draw()

    def _on_resize(self, _event=None):
        self._draw()

    def _draw(self):
        self.canvas.delete("all")
        width = self.canvas.winfo_width()

        # The widget may not have been laid out yet. Configure will redraw it.
        if width < 100:
            return

        if not self._stats:
            self.canvas.create_text(
                width / 2, self.height / 2,
                text="Waiting for live game data",
                fill=self.MUTED,
                font=("Arial", 14, "bold"),
                )
            return

        window, first_window, teams = self._stats
        if not window.frames or not first_window.frames:
            self.canvas.create_text(
                width / 2, self.height / 2,
                text="No game frames available",
                fill=self.MUTED,
                font=("Arial", 14, "bold"),
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
        total_seconds = max(0, int(elapsed.total_seconds()))
        game_time = f"{total_seconds // 60:02}:{total_seconds % 60:02}"

        self.canvas.configure(bg=self.BG)
        self.canvas.create_text(
            width / 2, 20,
            text=f"LIVE  •  GAME TIME {game_time}",
            fill=self.GOLD,
            font=("Arial", 11, "bold"),
            )

        margin, gap = 24, 18
        y1, y2 = 42, self.height - 14
        panel_width = (width - 2 * margin - gap) / 2

        blue_box = (margin, y1, margin + panel_width, y2)
        red_box = (margin + panel_width + gap, y1, width - margin, y2)

        self._draw_team(blue_box, blue_name, blue, self.BLUE)
        self._draw_team(red_box, red_name, red, self.RED)

    def _draw_team(self, box, name, team, accent):
        x1, y1, x2, y2 = box
        center_x = (x1 + x2) / 2

        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=self.PANEL,
            outline="#2a3949",
        )
        self.canvas.create_rectangle(
            x1, y1, x1 + 5, y2,
            fill=accent,
            outline=accent,
                    )

        self.canvas.create_text(
            center_x, y1 + 21,
            text=str(name).upper(),
            fill=self.TEXT,
            font=("Arial", 15, "bold"),
            width=x2 - x1 - 28,
                      )
        self.canvas.create_text(
            center_x, y1 + 50,
            text=f"{team.totalKills} KILLS",
            fill=accent,
            font=("Arial", 22, "bold"),
                      )

        dragons = ", ".join(team.dragons) if team.dragons else "—"
        stats = (
            f"TOWERS  {team.towers}      INHIBITORS  {team.inhibitors}\n"
            f"BARONS  {team.barons}      GOLD  {team.totalGold:,}\n"
            f"DRAGONS  {dragons}"
        )
        self.canvas.create_text(
            center_x, y1 + 96,
            text=stats,
            fill=self.MUTED,
            font=("Arial", 10, "bold"),
            justify="center",
            width=x2 - x1 - 28,
                      )