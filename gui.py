import pygame

class HealthBar:
    def __init__(self):
        self.bk_rect = pygame.Rect(30, 30, 80, 20)
        self.bk2_rect = pygame.Rect(32, 32, 76, 16)
        self.cl_rect = pygame.Rect(32, 32, 76, 16)
        self.color = "#00ff00"

    def update(self, app):
        if app.player.hp < 33:
            self.color = "#ff0000"
        elif app.player.hp < 67:
            self.color = "#ffee00"
        elif app.player.hp < 100:
            self.color = "#00ee00"
        else:
            self.color = "#10ff10"

        self.cl_rect.w = max(1, int(76 / (100 / app.player.hp)))

    def render(self, canvas):
        canvas.create_rectangle(self.bk_rect.x, self.bk_rect.y,
            self.bk_rect.right, self.bk_rect.bottom, fill="black")
        canvas.create_rectangle(self.bk2_rect.x, self.bk2_rect.y,
            self.bk_rect.right, self.bk_rect.bottom, fill="#204020")
        canvas.create_rectangle(self.cl_rect.x, self.cl_rect.y,
            self.cl_rect.right, self.cl_rect.bottom, fill=self.color,
             outline=self.color)
