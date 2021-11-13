import pygame
import math, random
import dataclasses
import gui

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

        self.rect.x = self.pos[0]
        self.rect.y = self.pos[1]

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
            app.player.get_hurt(30)
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
  
class Archer(Entity): #shoots projectiles
    Projectile = dataclasses.make_dataclass("Projectile",
     ["x", "y", "dx", "dy", "rect", "infected"])

    def __init__(self, x=0, y=0):
        super().__init__(x=x, y=y)

        self.mode = 'idle'
        self.mode2 = 'idle'
        self.mode_ticker = 0
        self.mode_ticker2 = 0
        self.circle_dist = 250
        self.arrows = []
        self.goal = [0, 0]
        self.goal2 = [0, 0]
        self.clockwise = random.choice([True, False]) #movement direction
        self.fire_rate = 50
        self.color = "#cc0066"

    def accept_stimuli(self, app):
        #run away if touching player
        if self.rect.colliderect(app.player.rect): 
            self.mode = 'goto'
            self.goal = [random.randrange(0, 700), random.randrange(0, 700)]
            self.mode_ticker = 0
        else:
            if self.mode == 'idle':
                if self.i_vel != [0, 0]: #stop when idle
                    self.i_vel = [0, 0]
                elif self.mode_ticker % 200 > 198:
                    self.mode = 'circle'
                    self.mode_ticker = 0
                    self.goal = [app.player.pos[0], app.player.pos[1]]

            elif self.mode == 'circle':
                if self.bounded or\
                     (self.mode_ticker % 50 == 0 and random.random() < 0.07):
                    self.mode_ticker = 0
                    if random.random() < 0.64 and not self.bounded:
                        self.mode = 'idle'
                    else:
                        self.mode = 'goto'
                        self.goal = [app.player.pos[0], app.player.pos[1]]

            elif self.mode == 'goto':
                if self.mode_ticker % 200 == 0:
                    self.mode_ticker = 0
                    if random.random() < 0.64:
                        self.mode = 'circle'
                        self.goal = [app.player.pos[0], app.player.pos[1]]
                    else:
                        self.mode = 'idle'
                elif self.bounded:
                    self.goal = [random.randrange(0, 700), random.randrange(0, 700)]
            else:
                self.mode = 'idle'

            if self.mode2 == 'shooting': #randomly start/stop shooting
                if random.random() < 0.07:
                    self.mode2 = 'idle'
                    self.mode_ticker2 = 0
            else:
                if random.random() < 0.1:
                    self.mode2 = 'shooting'
            
    def mode_act(self, app):
        self.mode_ticker += 1
        self.mode_ticker2 += 1

        if self.mode == 'circle': #circle player
            angle = math.atan2(app.player.pos[1] - self.pos[1],
                     app.player.pos[0] - self.pos[0])

            #find tangent to circle around player
            if self.clockwise:
                r_angle = angle - math.pi / 2
            else:
                r_angle = angle + math.pi / 2 
                
            dist = math.sqrt(pow(self.pos[0] - app.player.pos[0],2) +\
                     pow(self.pos[1] - app.player.pos[1],2))

            #move by tangent, speed increases with proximity to player
            self.i_vel[0] = (400 / max(dist, 40)) * math.cos(r_angle)
            self.i_vel[1] = (400 / max(dist, 40)) * math.sin(r_angle)
            
        elif self.mode == 'goto': #dash to a random location on screen
            if self.mode_ticker == 0:
                angle = math.atan2(self.goal[1] - self.pos[1],
                     self.goal[0] - self.pos[0])
                angle += random.random() * 2 - 1
                multiplier = random.randint(100, 200)
                
                self.goal = [self.pos[0] + math.cos(angle) * multiplier,
                                self.pos[1] + math.sin(angle) * multiplier]

            self.i_vel[0] = (self.goal[0] - self.pos[0]) / 120
            self.i_vel[1] = (self.goal[1] - self.pos[1]) / 120

        self.do_shoot(app)
        self.update_arrows(app)

    #manage shooting per turn
    def do_shoot(self, app):
        if self.mode2 == 'shooting':
            if self.mode_ticker2 % self.fire_rate == 0:
                angle = math.atan2(app.player.pos[1] - self.pos[1],
                     app.player.pos[0] - self.pos[0])

                # shoot 3 arrows at player,
                # two arrows pi/6 rad in each direction
                self.make_arrow(3 * math.cos(angle),
                 3 * math.sin(angle))
                self.make_arrow(3 * math.cos(angle - math.pi / 7),
                 3 * math.sin(angle - math.pi / 7))
                self.make_arrow(3 * math.cos(angle + math.pi / 7),
                 3 * math.sin(angle + math.pi / 7))

    #add 1 arrow to self.arrows
    def make_arrow(self, dx, dy):
        arrow = Archer.Projectile(x=self.pos[0], y=self.pos[1],
                                dx=dx, dy=dy, rect=None, infected=False)
        arrow.rect = pygame.Rect(arrow.x, arrow.y, 8, 8)
        self.arrows.append(arrow)

    def update_arrows(self, app):
        #move arrows
        for i, a in enumerate(self.arrows):
            a.x += a.dx * app.deltaTime
            a.y += a.dy * app.deltaTime
            a.rect.x = a.x
            a.rect.y = a.y

            #delete arrow if hits player
            if a.rect.colliderect(app.player.rect):
                if a.infected:
                    app.player.get_hurt(15)
                else:
                    app.player.get_hurt(10)

                del self.arrows[i]

        #delete oldest round when cap is reached
        if len(self.arrows) > 38:
            for i in range(3):
                del self.arrows[0]

    def render(self, canvas):
        super().render(canvas)
        for arrow in self.arrows: #draw arrows too
            if arrow.infected:
                canvas.create_rectangle(arrow.rect.x, arrow.rect.y,
                arrow.rect.right, arrow.rect.bottom, fill="#ff8888")
            else:
                canvas.create_rectangle(arrow.rect.x, arrow.rect.y,
                arrow.rect.right, arrow.rect.bottom, fill="#ffffff")

class WeirdArcher(Archer):
    def __init__(self, x=0, y=0):
        super().__init__(x=x, y=y)
        self.color = "#cc77ff"

    def mode_act(self, app):
        super().mode_act(app)
        #randomly rush player
        if random.random() < 0.004 and self.mode != 'goto':
            self.mode = 'goto'
            self.goal = app.player.pos.copy()
            self.mode_ticker = 0

    def do_shoot(self, app):
        #always shooting in a nonsensical direction
        if self.mode_ticker2 % (self.fire_rate // 2) == 0:
            angle = math.atan2(app.player.pos[1] - self.pos[1],
                    app.player.pos[0] - self.pos[0])
            angle = math.degrees(angle) #one minor change
            self.make_arrow(3 * math.cos(angle),
                3 * math.sin(angle))
            self.make_arrow(3 * math.cos(angle - math.pi / 7),
                3 * math.sin(angle - math.pi / 7))
            self.make_arrow(3 * math.cos(angle + math.pi / 7),
                3 * math.sin(angle + math.pi / 7))

class Vortal(Entity):
    def __init__(self, x=0, y=0):
        super().__init__(x=x, y=y)
        self.color = "#ffdd10"
        self.mode = 'idle'
        self.mode_ticker = 0
        self.mode_ticker2 = 500
        self.arrows = []
        self.angle_tilt = 0
        self.fire_rate = 30

    def accept_stimuli(self, app):
        if len(self.arrows) > 2 and self.rect.colliderect(app.player.rect):
            self.mode = 'gravity'
            self.mode_ticker = 0
        elif self.mode == 'idle':
            if self.mode_ticker % 400 == 0 or random.random() < (self.mode_ticker % 1000) / 1000:
                if len(self.arrows) == 0:
                    self.mode = 'seize'
                else:
                    self.mode = random.choice(['gravity', 'antigravity'])
                self.mode_ticker = 0
            elif self.mode_ticker2 == 0:
                self.pos = [random.choice(app.entities).pos[0],
                           random.choice(app.entities).pos[1]]
                self.mode_ticker2 = 500
                self.mode_ticker = 0
        elif self.mode == 'seize':
            if self.mode_ticker > 400 or random.random() < (self.mode_ticker % 1000) / 1000:
                self.mode = random.choice(['gravity', 'antigravity'])
                self.mode_ticker = 0
        elif self.mode == 'gravity':
            if len(self.arrows) == 0 or\
                 self.mode_ticker % 500 == 0 or\
                 (self.rect.colliderect(self.arrows[0].rect) and
                 self.rect.colliderect(self.arrows[len(self.arrows) // 2].rect)) :
                self.mode = random.choice(['spray', 'antigravity'])
                self.mode_ticker = 0
        elif self.mode == 'antigravity':
            if len(self.arrows) == 0:
                self.mode = 'seize'
                self.mode_ticker = 0
            elif self.mode_ticker % 400 == 0:
                self.mode = random.choice(['idle', 'gravity'])
                self.mode_ticker = 0
        elif self.mode == 'spray':
            if len(self.arrows) == 0 or self.mode_ticker % 302 > 300:
                self.mode = 'seize'
                self.mode_ticker = 0
        else:
            self.mode = 'idle'
            self.mode_ticker = 0

    def mode_act(self, app):
        self.mode_ticker += 1
        self.mode_ticker2 -= 1
        self.angle_tilt += random.randint(-3, 3) * 0.05

        if self.mode == 'seize':
            if self.mode_ticker % 3 != 0:
                for e in app.entities:
                    if isinstance(e, Archer):
                        if len(e.arrows) > 0:
                            arrow = random.choice(e.arrows)
                            arrow.infected = True
                            if arrow not in self.arrows:
                                self.arrows.append(arrow)
        elif self.mode == 'gravity':
            if self.mode_ticker == 0:
                for arrow in self.arrows:
                    angle = math.atan2(self.pos[1] - arrow.y, self.pos[0] - arrow.x)
                    arrow.dx = math.cos(angle) * 3 #attract arrows
                    arrow.dx = math.sin(angle) * 3
        elif self.mode == 'antigravity':
            if self.mode_ticker == 0:
                for arrow in self.arrows:
                    angle = math.atan2(self.pos[1] - arrow.y, self.pos[0] - arrow.x)
                    arrow.dx = -math.cos(angle) * 3 #send arrows away
                    arrow.dx = -math.sin(angle) * 3
        elif self.mode == 'spray':
            if self.mode_ticker % self.fire_rate == 1:
                if len(self.arrows) >= 8:
                    for i in range(8):
                        self.arrows[i].dx = 5 * math.cos(self.angle_tilt + i * math.pi / 8)
                        self.arrows[i].dy = 5 * math.sin(self.angle_tilt + i * math.pi / 8)
                if len(self.arrows) >= 6:
                    for i in range(6):
                        self.arrows[i].dx = 6 * math.cos(self.angle_tilt + i * math.pi / 6)
                        self.arrows[i].dy = 6 * math.sin(self.angle_tilt + i * math.pi / 6)
                elif len(self.arrows) >= 5: 
                    for i in range(5):
                        self.arrows[i].dx = 6 * math.cos(self.angle_tilt + i * math.pi / 5)
                        self.arrows[i].dy = 6 * math.sin(self.angle_tilt + i * math.pi / 5)
                elif len(self.arrows) >= 3:
                    for i in range(3):
                        self.arrows[i].dx = 7 * math.cos(self.angle_tilt + i * math.pi / 3)
                        self.arrows[i].dy = 7 * math.sin(self.angle_tilt + i * math.pi / 3)
            else:
                arrow = random.choice(self.arrows)
                arrow.infected = False
                self.arrows.remove(arrow)

        if len(self.arrows) > 30:
            for _ in range(3):
                arrow = random.choice(self.arrows)
                arrow.infected = False
                self.arrows.remove(arrow)

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
                self.make_trap()
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
            self.make_trap()

        self.update_traps(app)

    def make_trap(self):
        t = Trapper.Trap(x=self.pos[0], y=self.pos[1], range=60,
         rect=None, timer=200)
        t.rect = pygame.Rect(t.x, t.y, 10, 10)
        self.traps.append(t)

    def update_traps(self, app):
        for i, t in enumerate(self.traps):
            dist = math.sqrt(pow(t.x - app.player.pos[0],2) +\
               pow(t.y - app.player.pos[1],2))
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
                app.player.get_hurt(33)

    def render(self, canvas):
        for t in self.traps:
            canvas.create_rectangle(t.rect.x, t.rect.y,
                t.rect.right, t.rect.bottom, fill="#585840")
        super().render(canvas)

    @staticmethod
    def render_explosions(canvas):
        for ex in Trapper.explosions:
            canvas.create_oval(
                ex.x - ex.r, ex.y - ex.r,
                ex.x + ex.r, ex.y + ex.r,
                fill="red", outline="yellow"
            )

class Rifleman(Archer):
    def __init__(self, x=0, y=0):
        super().__init__(x=x, y=y)
        self.color = "#990033"
        self.fire_rate = 50

    #manage shooting per turn
    def do_shoot(self, app):
        if self.mode2 == 'shooting':
            if int(math.sqrt(self.mode_ticker2 % self.fire_rate)) == 0:
                angle = math.atan2(app.player.pos[1] - self.pos[1] +
                        app.player.i_vel[1] + app.player.e_vel[1],
                    app.player.pos[0] - self.pos[0] + app.player.i_vel[0] +
                        app.player.e_vel[0])

                # shoot fast arrow arrows at player
                self.make_arrow(10 * math.cos(angle),
                    10 * math.sin(angle))

    def update_arrows(self, app):
        #move arrows
        for i, a in enumerate(self.arrows):
            a.x += a.dx * app.deltaTime
            a.y += a.dy * app.deltaTime
            a.dx *= 1.009
            a.dy *= 1.009
            a.rect.x = a.x
            a.rect.y = a.y

            #delete arrow if hits player
            if a.rect.colliderect(app.player.rect):
                if a.infected:
                    app.player.get_hurt(22)
                else:
                    app.player.get_hurt(26)

                del self.arrows[i]

        #delete oldest round when cap is reached
        if len(self.arrows) > 16:
            del self.arrows[0]

class Laser:
    def __init__(self, start=(0,0), angle=0, speed=4, length=0, width=7, color="#50ffff"):
        self.startx = start[0] 
        self.starty = start[1]
        self.angle = angle
        self.speed = speed
        self.length = length
        self.endx = start[0] + math.cos(self.angle) * self.length 
        self.endy = start[1] + math.sin(self.angle) * self.length 
        self.timer = 0
        self.switch = True
        self.width = width
        self.color = color
        self.anchored = True

    def update(self, app, dtheta=0, power=50):
        self.length += self.speed * app.deltaTime
        self.angle += dtheta
        self.timer += 1
        
        if not self.anchored:
            self.startx += math.cos(self.angle) * self.speed
            self.starty += math.sin(self.angle) * self.speed
            self.endx += self.speed + math.cos(self.angle)
            self.endy += self.speed + math.sin(self.angle)
        else:
            self.endx = self.startx + math.cos(self.angle) * self.length
            self.endy = self.starty + math.sin(self.angle) * self.length

        if self.timer % 70:
            self.switch = not self.switch

    def detect_laser_wall_hit(self, start, end):
        d = (start[0] - end[0]) * (self.starty - self.endy) -\
            (start[1] - end[1]) * (self.startx - self.endx)
        t = (start[0] - self.startx) * (self.starty - self.endy) -\
            (start[1] - self.starty) * (self.startx - self.endx)
        u = (start[0] - self.startx) * (start[1] - end[1]) -\
            (start[1] - self.starty) * (start[0] - end[0])

        t /= d
        u /= d

        if 0 <= t and t <= 1 and 0 <= u and t <= 1:
            return True
        return False

    def render(self, canvas):
        canvas.create_line(self.startx, self.starty, self.endx, self.endy,
        width=self.width, fill=self.color)

class Lancer(Entity):
    def __init__(self, x=0, y=0):
        super().__init__(x=x, y=y)
        self.mode = 'idle'
        self.shooting = False
        self.mode_ticker = 0
        self.mode_ticker2 = 0
        self.circle_dist = 250
        self.l_width = 12
        self.goal = [0, 0]
        self.goal2 = [0, 0]
        self.clockwise = random.choice([True, False]) #movement direction
        self.lance = Laser(self.pos, 0, 0, 60, 7, "#ffffff")
        self.fire_rate = 50
        self.charge_timer = 0
        self.color = "#bfaaff"
        self.speed = 2

    def accept_stimuli(self, app):
        #run away if touching player
        if self.rect.colliderect(app.player.rect): 
            self.mode = 'goto'
            self.mode_ticker = 0
            self.goal = [random.randrange(200, 700), random.randrange(200, 700)]
        else:
            if self.mode == 'idle':
                if self.i_vel != [0, 0]: #stop when idle
                    self.i_vel = [0, 0]
                elif self.mode_ticker % 200 > 198:
                    self.mode = 'circle'
                    self.mode_ticker = 0
                    self.goal = [app.player.pos[0], app.player.pos[1]]
                    self.speed = random.randint(180, 501)
                    self.clockwise = not self.clockwise
                elif self.mode_ticker % 111 > 298:
                    self.goal = app.player.pos.copy()
                    self.mode = 'goto'
                    self.mode_ticker = 0
            elif self.mode == 'circle':
                if self.bounded or\
                     (self.mode_ticker % 50 == 0 and random.random() < 0.07):
                    self.mode_ticker = 0
                    if random.random() < 0.24 and not self.bounded:
                        self.mode = 'idle'
                    else:
                        self.charge_timer = 200
                        self.mode = 'goto'
                        self.goal = app.player.pos.copy()

            elif self.mode == 'goto':
                if self.mode_ticker % 100 == 0:
                    self.mode_ticker = 0
                    if random.random() < 0.64:
                        self.mode = 'circle'
                        self.goal = [app.player.pos[0], app.player.pos[1]]
                    else:
                        self.mode = 'idle'
            else:
                self.mode = 'idle'

    def mode_act(self, app):
        self.mode_ticker += 1
        self.mode_ticker2 += 1
        if self.charge_timer > 0:
            self.charge_timer -= 1

        dist = math.sqrt(pow(self.pos[0] - app.player.pos[0],2) +\
                     pow(self.pos[1] - app.player.pos[1],2))

        if self.mode == 'circle': #circle player
            angle = math.atan2(app.player.pos[1] - self.pos[1],
                    app.player.pos[0] - self.pos[0])
            #find tangent to circle around player
            if self.clockwise:
                r_angle = angle - math.pi / 2.09
            else:
                r_angle = angle + math.pi / 2.09

            #move by tangent, speed increases with proximity to player
            self.i_vel[0] = (self.speed / max(dist, 40)) * math.cos(r_angle)
            self.i_vel[1] = (self.speed / max(dist, 40)) * math.sin(r_angle)
            
        elif self.mode == 'goto': #dash to a random location on screen
            if self.mode_ticker == 0:
                angle = math.atan2(self.goal[1] - self.pos[1],
                    self.goal[0] - self.pos[0])
                multiplier = random.randint(100, 200)
                
                self.goal = [self.pos[0] + math.cos(angle) * multiplier,
                                self.pos[1] + math.sin(angle) * multiplier]

                self.lance.angle = angle

            self.i_vel[0] = (self.goal[0] - self.pos[0]) / 12000 * self.speed
            self.i_vel[1] = (self.goal[1] - self.pos[1]) / 12000 * self.speed

        #manage lance
        self.lance.startx = self.pos[0] + self.rect.w // 2
        self.lance.starty = self.pos[1] + self.rect.h // 2
        angle = math.atan2(app.player.pos[1] - self.pos[1],
                            app.player.pos[0] - self.pos[0])
        if self.mode == 'circle':
            if dist > 80:
                if self.lance.angle > angle:
                    self.lance.angle -= math.pi / 90
                elif self.lance.angle < angle:
                    self.lance.angle += math.pi / 90
            else:
                if self.clockwise:
                    self.lance.angle = angle - 90
                else:
                    self.lance.angle = angle + 90
            
        self.lance.update(app)

    def render(self, canvas):
        if self.charge_timer % 3 == 1:
            canvas.create_rectangle(self.rect.x, self.rect.y,
             self.rect.right, self.rect.bottom, outline="#ffffff")
        else:
            super().render(canvas)
        self.lance.render(canvas)

class Laserist(Entity):
    def __init__(self, x=0, y=0):
        super().__init__(x=x, y=y)
        self.mode = 'idle'
        self.mode_ticker = 0
        self.mode_ticker2 = 0
        self.circle_dist = 250
        self.l_width = 12
        self.lasers = []
        self.goal = [0, 0]
        self.goal2 = [0, 0]
        self.clockwise = random.choice([True, False]) #movement direction
        self.laser_clockwise = random.choice([True, False])
        self.fire_rate = 50
        self.color = "#44aaaa"
        self.speed = 2
        self.laser_countdown = 90

    def accept_stimuli(self, app):
        #run away if touching player
        if self.rect.colliderect(app.player.rect): 
            self.mode = 'goto'
            self.mode_ticker = 0
        else:
            if self.mode == 'idle':
                if self.i_vel != [0, 0]: #stop when idle
                    self.i_vel = [0, 0]
                elif self.mode_ticker % 200 > 198:
                    self.mode = 'circle'
                    self.mode_ticker = 0
                    self.goal = [app.player.pos[0], app.player.pos[1]]
                    self.speed = random.randint(180, 501)

            elif self.mode == 'circle':
                if self.bounded or\
                     (self.mode_ticker % 50 == 0 and random.random() < 0.07):
                    self.mode_ticker = 0
                    if random.random() < 0.64 and not self.bounded:
                        self.mode = 'idle'
                    else:
                        self.mode = 'goto'

            elif self.mode == 'goto':
                if self.mode_ticker % 200 == 0:
                    self.mode_ticker = 0
                    if random.random() < 0.64 and not self.bounded:
                        self.mode = 'circle'
                        self.goal = [app.player.pos[0], app.player.pos[1]]
                    else:
                        self.mode = 'idle'
            else:
                self.mode = 'idle'

            #randomly start/stop shooting
            if self.mode_ticker2 % 400 == 0 or self.laser_countdown < -460:
                self.laser_countdown += 360


    def mode_act(self, app):
        self.mode_ticker += 1
        self.mode_ticker2 += 1
        self.laser_countdown -= 1
        
        dist = math.sqrt(pow(self.pos[0] - app.player.pos[0],2) +\
                pow(self.pos[1] - app.player.pos[1],2))

        if self.mode == 'circle': #circle player
            angle = math.atan2(app.player.pos[1] - self.pos[1],
                    app.player.pos[0] - self.pos[0])
            #find tangent to circle around player
            if self.clockwise:
                r_angle = angle - math.pi / 2
            else:
                r_angle = angle + math.pi / 2

            #move by tangent, speed increases with proximity to player
            self.i_vel[0] = (self.speed / max(dist, 40)) * math.cos(r_angle) / 1.3
            self.i_vel[1] = (self.speed / max(dist, 40)) * math.sin(r_angle) / 1.3
            
        elif self.mode == 'goto': #dash to a random location on screen
            if self.mode_ticker == 0:
                angle = math.atan2(app.player.pos[1] - self.pos[1],
                     app.player.pos[0] - self.pos[0])
                angle += random.random() * 2 - 1
                multiplier = random.randint(100, 200)
                
                self.goal = [self.pos[0] + math.cos(angle) * multiplier,
                                self.pos[1] + math.sin(angle) * multiplier]

            self.i_vel[0] = (self.goal[0] - self.pos[0]) / 15000 * self.speed
            self.i_vel[1] = (self.goal[1] - self.pos[1]) / 15000 * self.speed


        #manage shooting toggle
        if self.laser_countdown < 0 and self.mode != 'goto':
            if self.mode_ticker2 % self.fire_rate == 0:
                if len(self.lasers) == 0:
                    angle = math.atan2(app.player.pos[1] - self.pos[1],
                                app.player.pos[0] - self.pos[0])
                    self.lasers.append(Laser([self.pos[0] + self.rect.w // 2,
                     self.pos[1] + self.rect.h // 2], angle, 13, 0))
                else:
                    self.lasers.clear()

        #update all lasers
        for l in self.lasers:
            l.startx = self.pos[0] + self.rect.w // 2
            l.starty = self.pos[1] + self.rect.h // 2
            if self.mode == 'circle':
                angle = math.atan2(app.player.pos[1] - self.pos[1],
                                app.player.pos[0] - self.pos[0])
                if l.angle > angle:
                    l.angle -= (math.pi / 1700 / max(1, math.sqrt(dist) * 20)) * app.deltaTime
                elif l.angle < angle:
                    l.angle += (math.pi / 1700 / max(1, math.sqrt(dist) * 20)) * app.deltaTime
                    
            l.update(app)
            self.e_vel[0] -= math.cos(l.angle) / 3
            self.e_vel[1] -= math.sin(l.angle) / 3

    def render(self, canvas):
        for l in self.lasers:
            l.render(canvas)
        if self.laser_countdown % 3 == 0 and self.laser_countdown < 50 and self.laser_countdown >= 0:
            canvas.create_rectangle(self.rect.x, self.rect.y,
             self.rect.right, self.rect.bottom, outline="#ffffff")
        else:
            super().render(canvas)

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
            elif dist < 25 and random.random() < 0.5:
                self.goal[0] = random.randrange(200, 500)
                self.goal[1] = random.randrange(200, 500)
            elif dist2 < 175:
                self.goal = app.player.pos.copy()
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
            fp.rect.x = fp.x - round(fp.size // 2)
            fp.rect.y = fp.y - round(fp.size // 2)
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
            
class GhostArcher:
    def __init__(self):
        self.invisiblity = True
