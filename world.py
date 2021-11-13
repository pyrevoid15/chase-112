import pygame, random
from cmu_112_graphics import *

class Bush:
    healthy_color = "#40aa30"
    damaged_color = "#302000"
    def __init__(self, app):
        self.pos = [random.randrange(app.world_left + 20, app.world_right - 60),
            random.randrange(app.world_top + 20, app.world_bottom - 60)]
        self.rect = pygame.Rect(self.pos[0], self.pos[1], 40, 40)
        self.damaged = False
        self.hp = 100
                
class Map:
    colors = ["#00c800", "#009614", "#149614", "#0ac800", "#00c800"]
    
    def __init__(self, app, bushes=True):
        self.grid = []
        for y in range(app.world_bottom // 15 + 3):
            row = []
            for x in range(app.world_right // 15 + 3):
                row.append(random.randint(0, 4))
            self.grid.append(row)
            
        self.bushes = []
        if bushes:
            for _ in range(random.randint(
                    min(app.world_right - app.world_left,
                        app.world_bottom - app.world_top) // 60,
                    max(app.world_right - app.world_left,
                        app.world_bottom - app.world_top) // 60)):
                self.bushes.append(Bush(app))
                
        self.image = Image.new('RGB', (len(self.grid) * 30, len(self.grid[0]) * 30), (0, 0, 0))
        self.crayon = ImageDraw.Draw(self.image)
        
        for y in range(len(self.grid)):
            for x in range(len(self.grid[0])):
                col = Map.colors[self.grid[y][x]]
                self.crayon.rectangle(
                    (x * 30, y * 30, x * 30 + 30, y * 30 + 30),
                    fill=col, width=0)
                
        self.rimage = ImageTk.PhotoImage(self.image)
    
    def update(self, app):
        for b in self.bushes:
            b.rect.x = b.pos[0] - app.camera[0]
            b.rect.y = b.pos[1] - app.camera[1]
            
            if b.hp < 200:
                b.hp += 1
                if b.hp < 0:
                    b.damaged = True
                else:
                    b.damaged = False
            
    def render_bushes(self, app, canvas):
        screen_rect = pygame.Rect(0, 0, app.width, app.height)
        for b in self.bushes:
            if b.rect.colliderect(screen_rect):
                if b.damaged:
                    canvas.create_rectangle(b.rect.x, b.rect.y,
                        b.rect.right, b.rect.bottom, fill=Bush.damaged_color)
                else:
                    canvas.create_rectangle(b.rect.x, b.rect.y,
                        b.rect.right, b.rect.bottom, fill=Bush.healthy_color)
        
    def render_background(self, app, canvas):
        canvas.create_image(-app.camera[0], -app.camera[1], image=self.rimage)
    