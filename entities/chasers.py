import pygame
import random, math
from entities.entity import Entity

class Chaser(Entity):
    def __init__(self, x=0, y=0) -> None:
        super().__init__(x=x, y=y)
        self.mode = 'chase'
        self.mode_ticker = 0
        self.switch_readiness = 100
        self.goal = [0, 0]

        #to introduce variability to individual attack patterns
        self.chase_period = random.randint(97, 103)
        self.charge_intensity = 0.95 + random.random() / 4

    def accept_stimuli(self, app): #change modes depending on stimuli
        if self.rect.colliderect(app.player.rect):
            self.mode = 'idle'
            self.mode_ticker = 0
            app.player.get_hurt(app, 30, f"Player was hit by chaser in {self.mode} for 30 damage.")
        else:
            if self.mode == 'chase':
                if self.mode_ticker >= 5 * self.chase_period:
                    self.mode = 'charge'
                    self.mode_ticker = 0
                elif self.mode_ticker == int(4.5 * self.chase_period):
                    self.switch_readiness = 50
            elif self.mode == 'charge':
                if self.mode_ticker >= 4 * self.chase_period and random.random() < 0.1:
                    self.mode = 'chase'
                    self.charge_intensity = 1
                    self.mode_ticker = 0
                elif math.sqrt(pow(self.pos[0] - app.player.pos[0],2) +\
                     pow(self.pos[1] - app.player.pos[1],2)) > 3 * self.chase_period:
                    self.mode = 'chase'
                    self.mode_ticker = 0
            elif self.mode == 'idle':
                if self.mode_ticker >= 2 * self.chase_period:
                    self.mode = 'chase'
                    self.mode_ticker = 0
                elif self.i_vel[0] != 0 or self.i_vel[1] != 0:
                    self.i_vel = [0, 0]
            else:
                self.mode = 'chase'

    def mode_act(self, app): #direct mode-specific behaviors
        self.mode_ticker += 1 #increment/decrement timer values
        if self.switch_readiness > 0:
            self.switch_readiness -= 1

        if self.mode == 'chase': #move stratght toward player
            self.i_vel[0] = (app.player.pos[0] - self.pos[0]) / 400
            self.i_vel[1] = (app.player.pos[1] - self.pos[1]) / 400
        elif self.mode == 'charge': #move straight towards a goal
            if self.mode_ticker == 0:
                self.goal[0] = (app.player.pos[0] - self.pos[0] +
                 app.player.vel[0] * 2)
                self.goal[1] = (app.player.pos[1] - self.pos[1] +
                 app.player.vel[1] * 2)
                d = math.sqrt(pow(self.pos[0] - self.goal[0],2) +\
                     pow(self.pos[1] - self.goal[1],2))

                angle = math.atan2(self.goal[1], self.goal[0]) 
                self.i_vel[0] = (100 * math.cos(angle) * max(d / 70, 1) +\
                     (self.goal[0] - self.pos[0]) / 250) * self.charge_intensity
                self.i_vel[1] = (100 * math.sin(angle) * max(d / 70, 1) +\
                     (self.goal[1] - self.pos[1]) / 250) * self.charge_intensity
            else:
                self.i_vel[0] *= 1.007
                self.i_vel[1] *= 1.007

    def render(self, canvas): 
        #flash just before charging
        if self.switch_readiness % 5 == 1 and self.mode == 'chase': 
            canvas.create_rectangle(self.rect.x, self.rect.y, self.rect.right,
             self.rect.bottom, fill="#ffffff")
        elif self.invincibility % 6 != 1:
            canvas.create_rectangle(self.rect.x, self.rect.y, self.rect.right,
             self.rect.bottom, fill=self.color)

class TChaser(Chaser): #a Chaser that occasionally teleports
    def __init__(self, x=0, y=0):
        super().__init__(x=x, y=y)
        self.t_goal = [0, 0]
        self.teleport_counter = 80
        self.color = "#0d0da0" #navy blue

    def teleport(self, app, inclusive=False): 
        #get average position of all Chasers
        
        avg_pos = [0, 0]
        cc = 0
        for ap in app.entities:
            if isinstance(ap, Chaser) or inclusive:
                cc += 1
                avg_pos[0] += ap.pos[0]
                avg_pos[1] += ap.pos[1]

        avg_pos[0] /= cc
        avg_pos[1] /= cc
        
        #and get a teleportation goal exactly opposite of that position
        angle = math.atan2(app.player.pos[0] - avg_pos[0], app.player.pos[1] - avg_pos[1])
        angle += math.pi

        multiplier = random.randrange(100, 300)
        self.t_goal[0] = app.player.pos[0] + math.cos(angle) * multiplier
        self.t_goal[1] = app.player.pos[1] + math.sin(angle) * multiplier
        self.teleport_counter = self.chase_period // 2

    def mode_act(self, app):
        if self.teleport_counter > 0:
            self.teleport_counter -= 1

        super().mode_act(app)
        #actually teleport
        if self.teleport_counter == 0:
            self.pos[0] = self.t_goal[0]
            self.pos[1] = self.t_goal[1]
            self.teleport_counter = -1 #lock teleportation until activation
        #teleport randomly
        elif random.random() < 0.05 and self.mode_ticker % (self.chase_period // 2) == 0:
            self.teleport(app)
        #teleport if touching another enemy
        elif self.mode_ticker % 5 == 0 and self.teleport_counter > 46: 
            for e in app.entities:
                if e is not self and e.rect.colliderect(self.rect):
                    self.teleport(app, True)


    def render(self, canvas):
        #flash just before teleporting
        if self.teleport_counter % 3 == 1:
            canvas.create_rectangle(self.rect.x, self.rect.y, self.rect.right,
             self.rect.bottom, fill="#0affff")
            canvas.create_rectangle(self.t_goal[0], self.t_goal[1],
             self.t_goal[0] + self.rect.w,
             self.t_goal[1] + self.rect.w, outline="#00ffff")
        else:
            super().render(canvas)
  