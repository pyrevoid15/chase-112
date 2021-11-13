import pygame
import math, random
import dataclasses
from entities.entity import Entity

class Trapper(Entity):
    Trap = dataclasses.make_dataclass("Trap", ["x", "y", "range", "rect", "timer"])
    Boom = dataclasses.make_dataclass("Boom", ["x", "y", "r", "max_r", "ex"])
    explosions = []

    def __init__(self, x=0, y=0):
        super().__init__(x=x, y=y)
        self.color = "#10732f"
        self.traps = []
        self.mode = 'idle'
        self.mode_ticker = 0
        self.fire_rate = 90
        self.goal = []

    def accept_stimuli(self, app):
        dist = math.sqrt(pow(self.pos[0] - app.player.pos[0],2) +\
               pow(self.pos[1] - app.player.pos[1],2))
        
        if self.mode == 'idle':
            if dist < 90:
                self.mode = 'flee'
                self.goal = app.player.pos.copy()
            elif self.mode_ticker > 400:
                self.mode = 'goto'
                self.mode_ticker = 0
                self.goal = [
                    random.randrange(100, 200) + app.player.pos[0],
                    random.randrange(100, 200) + app.player.pos[1]]
            else:
                self.i_vel = [0, 0]
        elif self.mode == 'flee':
            if self.mode_ticker > 100:
                self.mode = random.choice(['goto', 'idle'])
                self.mode_ticker = 0
                self.goal = [
                    random.randrange(100, 200) + app.player.pos[0],
                    random.randrange(100, 200) + app.player.pos[1]]
            elif dist > 200:
                self.mode = 'goto'
            elif self.bounded:
                self.make_trap(app)
                self.goal = [
                    random.randrange(100, 200) * random.choice([-1, 1]) + app.player.pos[0],
                    random.randrange(100, 200) * random.choice([-1, 1]) + app.player.pos[1]]
                self.mode = 'goto'
                self.mode_ticker = 0
                
                
        elif self.mode == 'goto':
            if self.mode_ticker > 300:
                self.mode = random.choice(['flee', 'idle'])
                self.mode_ticker = 0
                if self.mode == 'flee':
                    self.goal = app.player.pos.copy()
                else:
                    self.goal = [
                        random.randrange(100, 400) + self.pos[0],
                        random.randrange(100, 400) + self.pos[1]]
        else:
            self.mode = 'idle'

    def mode_act(self, app):
        self.mode_ticker += 1
        if self.mode == 'flee':
            dist = math.sqrt(pow(self.pos[0] - app.player.pos[0],2) +\
               pow(self.pos[1] - app.player.pos[1],2))
            angle = math.atan2(self.pos[1] - self.goal[1], self.pos[0] - self.goal[0])

            self.i_vel[0] = 2.1 * math.cos(angle) / max(1, dist / 200)
            self.i_vel[1] = 3.1 * math.sin(angle) / max(1, dist / 200)
        elif self.mode == 'goto':
            angle = math.atan2(self.goal[1] - self.pos[1], self.goal[0] - self.pos[0])

            self.i_vel[0] = 1.1 * math.cos(angle)
            self.i_vel[1] = 1.1 * math.sin(angle)

        if self.mode_ticker % self.fire_rate == 1:
            self.make_trap(app)

        self.update_traps(app)

    def make_trap(self, app):
        t = Trapper.Trap(x=self.pos[0], y=self.pos[1], range=60,
         rect=None, timer=200)
        t.rect = pygame.Rect(t.x - app.camera[0], t.y - app.camera[1], 10, 10)
        self.traps.append(t)

    def update_traps(self, app):
        for i, t in enumerate(self.traps):
            dist = math.sqrt(pow(t.x - app.player.pos[0],2) +\
               pow(t.y - app.player.pos[1],2))
            t.rect.x = t.x - app.camera[0]
            t.rect.y = t.y - app.camera[1]
            
            if dist < t.range or t.timer < 0:
                Trapper.explosions.append(
                    Trapper.Boom(x=t.x+5, y=t.y+5, r=10, max_r=t.range, ex=True)
                )
                del self.traps[i]

    @staticmethod
    def update_explosions(app):
        for i, ex in enumerate(Trapper.explosions):
            if ex.ex:
                ex.r += 2
            else:
                ex.r -= 3

            if ex.r > ex.max_r:
                ex.ex = False
            elif ex.r < 9:
                del Trapper.explosions[i]

            if math.sqrt(pow(ex.x - app.player.pos[0],2) +\
               pow(ex.y - app.player.pos[1],2)) < ex.r:
                app.player.get_hurt(app, 33, f"Player was caught in a trap for 33 damage.")
                
            for i, b in enumerate(app.map.bushes):
                if not b.damaged and math.sqrt(pow(ex.x - b.pos[0],2) +\
                        pow(ex.y - b.pos[1],2)) < ex.r:
                    if random.random() < 0.3:
                        del app.map.bushes[i]
                    else:
                        b.hp -= 300

    def render(self, canvas):
        for t in self.traps:
            canvas.create_rectangle(t.rect.x, t.rect.y,
                t.rect.right, t.rect.bottom, fill="#585840")
        super().render(canvas)

    @staticmethod
    def render_explosions(app, canvas):
        for ex in Trapper.explosions:
            canvas.create_oval(
                ex.x - ex.r - app.camera[0], ex.y - ex.r - app.camera[1],
                ex.x + ex.r - app.camera[0], ex.y + ex.r - app.camera[1],
                fill="red", outline="yellow"
            )

class Ghost(Entity):
    Footprint = dataclasses.make_dataclass("Footprint", ["x", "y", "timer", "size", "rect"])
    
    def __init__(self, x=0, y=0):
        super().__init__(x=x, y=y)
        
        self.invisiblity = 5
        self.visibility_period = random.randint(280, 480)
        self.goal = [0, 0]
        self.mode_ticker = 0
        self.mode = 'wander'
        self.speed = 0.5
        self.clockwise = random.choice([True, False])
        self.footsteps = []
        
    def accept_stimuli(self, app):
        dist = math.sqrt(pow(self.pos[0] - self.goal[0],2) +\
                pow(self.pos[1] - self.goal[1],2))
        dist2 = math.sqrt(pow(self.pos[0] - app.player.pos[0],2) +\
                pow(self.pos[1] - app.player.pos[1],2))
        
        if self.mode == 'wander':
            if self.mode_ticker % 150 == 0 and random.random() < 0.2:
                if dist < 175 and random.random() < 0.5:
                    self.goal = app.player.pos.copy()
                else:
                    self.goal[0] = random.randrange(200, 500)
                    self.goal[1] = random.randrange(200, 500)
            elif self.mode_ticker % 1044 == 1 and random.random() < 0.03:
                self.mode = 'circle'
                self.mode_ticker = 0
                if random.random() < 0.2:
                    self.goal = app.player.pos.copy()
                else:
                    ge = random.choice(app.entities).pos
                    i = 0
                    while ge == self.pos and i < 5:
                        i += 1
                        ge = random.choice(app.entities).pos
                        
                    if i < 5:
                        self.goal = ge.copy()
                    else:
                        self.goal = [random.randrange(200, 500), random.randrange(200, 500)]
            elif dist < 25 and random.random() < 0.5 and self.goal != app.player.pos:
                self.goal[0] = random.randrange(200, 500)
                self.goal[1] = random.randrange(200, 500)
            elif dist2 < 175:
                self.goal = app.player.pos.copy()
                if self.rect.colliderect(app.player.rect):
                    app.player.get_hurt(app, 20, f"Player was touched by a ghost in {self.mode} for 20 damage.")
        elif self.mode == 'circle':
            if self.mode_ticker % 99 == 0 and random.random() < 0.13:
                if random.random() < 0.45:
                    self.goal = app.player.pos.copy()
                elif random.random() < 0.7:
                    ge = random.choice(app.entities).pos
                    i = 0
                    while ge == self.pos and i < 5:
                        i += 1
                        ge = random.choice(app.entities).pos
                        
                    if i < 5:
                        self.goal = ge.copy()
                    else:
                        self.goal = [random.randrange(200, 500), random.randrange(200, 500)]
                        
                    if self.bounded: 
                        self.mode = 'wander'
                        
            elif self.mode_ticker % 642 == 8 and random.random() < 0.3:
                self.mode = 'wander'
                self.mode_ticker = 0
                self.goal[0] = random.randrange(200, 500)
                self.goal[1] = random.randrange(200, 500)
            elif dist < 175 and random.random() < 0.5:
                self.goal = app.player.pos.copy()
            elif self.bounded: 
                self.mode = 'wander'
                self.mode_ticker = 0
                self.goal[0] = random.randrange(200, 500)
                self.goal[1] = random.randrange(200, 500)
                
        else:
            self.mode = 'wander'
            
        if self.invisiblity < -800 + self.visibility_period // 3:
            self.invisiblity += 800 + self.visibility_period
            
    def mode_act(self, app):
        self.mode_ticker += 1
        self.invisiblity -= 1        
        
        if self.mode == 'wander':
            self.goal[0] += random.randrange(100, 650) * random.choice([-1, 1])
            self.goal[1] += random.randrange(100, 650) * random.choice([-1, 1])
            
            angle = math.atan2(self.goal[1] - self.pos[1], self.goal[0] - self.pos[0])
            
            self.i_vel[0] = math.cos(angle) * self.speed
            self.i_vel[1] = math.sin(angle) * self.speed
        elif self.mode == 'circle':
            angle = math.atan2(app.player.pos[1] - self.pos[1],
                    app.player.pos[0] - self.pos[0])
            #find tangent to circle around player
            if self.clockwise:
                r_angle = angle - math.pi / 3
            else:
                r_angle = angle + math.pi / 3

            dist = math.sqrt(pow(self.pos[0] - app.player.pos[0],2) +\
                     pow(self.pos[1] - app.player.pos[1],2))

            #move by tangent, speed increases with proximity to player
            self.i_vel[0] = (self.speed / (max(min(dist, 100), 40) * 16)) * math.cos(r_angle)
            self.i_vel[1] = (self.speed / (max(min(dist, 100), 40) * 16)) * math.sin(r_angle)
                
        if self.mode_ticker % 90 == 1:
            fp = Ghost.Footprint(x=self.pos[0], y=self.pos[1],
                                 timer=0, size=10, rect=None)
            fp.rect = pygame.Rect(fp.x - fp.size // 2, fp.y - fp.size // 2, fp.size, fp.size)
            self.footsteps.append(fp)
            
        for fp in self.footsteps:
            fp.size += 0.05
            fp.rect.x = fp.x - round(fp.size // 2) - app.camera[0]
            fp.rect.y = fp.y - round(fp.size // 2) - app.camera[1]
            fp.rect.w = fp.size
            fp.rect.h = fp.size
            
            if fp.size > 40:
                del self.footsteps[self.footsteps.index(fp)]
        
    def render(self, canvas):
        if self.invincibility % 6 == 1 or self.invisiblity >= 0:
            canvas.create_rectangle(self.rect.x, self.rect.y,
             self.rect.right, self.rect.bottom, outline="#ffffff")
        
        for fp in self.footsteps:
            canvas.create_oval(fp.rect.x, fp.rect.y, fp.rect.right, fp.rect.bottom, outline="#96b096")
            