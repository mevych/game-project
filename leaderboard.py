import os
import json
import pygame
from constants import COLOR_GOLD, COLOR_YELLOW, COLOR_WHITE, COLOR_GREY, SCREEN_WIDTH, SCREEN_HEIGHT


class Leaderboard:
    def __init__(self):
        self.filename = "highscores.json"
        self.scores = self.load_scores()

    def load_scores(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    return sorted(data, reverse=True)[:10]
            except Exception:
                return [0] * 5
        return [0] * 5

    def add_score(self, score):
        if score > 0:
            self.scores.append(score)
            self.scores = sorted(list(set(self.scores)), reverse=True)[:5]
            self.save_scores()

    def save_scores(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.scores, f)
        except Exception as e:
            print(f"Ошибка сохранения таблицы рекордов: {e}")

    def draw(self, surface, draw_button_callback):
        t_font = pygame.font.SysFont("Courier New", 36, bold=True)
        b_font = pygame.font.SysFont("Courier New", 22, bold=True)

        title = t_font.render("HIGHEST HIGH SCORES", True, COLOR_GOLD)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        y_offset = 180
        for i, score in enumerate(self.scores):
            col = COLOR_YELLOW if i == 0 else (COLOR_WHITE if score > 0 else COLOR_GREY)
            lbl = b_font.render(f"RANK {i + 1:02d} ........ {score:06d} PTS", True, col)
            surface.blit(lbl, (SCREEN_WIDTH // 2 - lbl.get_width() // 2, y_offset))
            y_offset += 40

        draw_button_callback(surface, "RETURN TO MENU", SCREEN_HEIGHT - 130, 0)