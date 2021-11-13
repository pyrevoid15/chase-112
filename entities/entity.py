import pygame

class Entity:
    def __init__(self, x=0, y=0) -> None:
        self.pos = [x, y]
        self.grid_pos = [x // 20, y // 20]
        self.i_vel = [0, 0] #player directed
        self.e_vel = [0, 0] #environment directed
        self.rect = pygame.Rect(self.pos[0], self.pos[0], 20, 20)
        self.color = "#000000"

        self.hp = 100
        self.invincibility = 10
        self.bounded = False

    def restrict_bounds(self, app):
        bounded = False
        
        if self.pos[0] < app.world_left:
            self.pos[0] = app.world_left
            bounded = True
        elif self.pos[0] + self.rect.w > app.world_right:
            self.pos[0] = app.world_right - self.rect.w
            bounded = True
            
        if self.pos[1] < app.world_top:
            self.pos[1] = app.world_top
            bounded = True
        elif self.pos[1] + self.rect.h > app.world_right:
            self.pos[1] = app.world_bottom - self.rect.h
            bounded = True
            
        return bounded

    def update_pos(self, app): #update position-related fields
        self.pos[0] += (self.i_vel[0] + self.e_vel[0]) * app.deltaTime
        self.pos[1] += (self.i_vel[1] + self.e_vel[1]) * 0.97 * app.deltaTime

        self.bounded = self.restrict_bounds(app)

        self.e_vel[0] /= 1.2
        self.e_vel[1] /= 1.2
        if abs(self.e_vel[0]) < 0.3:
            self.e_vel[0] = 0
        if abs(self.e_vel[1]) < 0.3:
            self.e_vel[1] = 0

        self.rect.x = self.pos[0] - app.camera[0]
        self.rect.y = self.pos[1] - app.camera[1]

    def accept_stimuli(self, app):
        pass

    def mode_act(self, app):
        pass

    def update(self, app): #update wrapper
        if self.invincibility > 0:
            self.invincibility -= 1
        self.accept_stimuli(app)
        self.mode_act(app)
        self.update_pos(app)

    def render(self, canvas): #render basic entity
        if self.invincibility % 6 != 1:
            canvas.create_rectangle(self.rect.x, self.rect.y,
             self.rect.right, self.rect.bottom, fill=self.color)
