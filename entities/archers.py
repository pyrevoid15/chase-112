import pygame
import dataclasses
import math, random
from entities.entity import Entity

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
                self.make_arrow(app, 3 * math.cos(angle),
                 3 * math.sin(angle))
                self.make_arrow(app, 3 * math.cos(angle - math.pi / 7),
                 3 * math.sin(angle - math.pi / 7))
                self.make_arrow(app, 3 * math.cos(angle + math.pi / 7),
                 3 * math.sin(angle + math.pi / 7))

    #add 1 arrow to self.arrows
    def make_arrow(self, app, dx, dy):
        arrow = Archer.Projectile(x=self.pos[0], y=self.pos[1],
                                dx=dx, dy=dy, rect=None, infected=False)
        arrow.rect = pygame.Rect(arrow.x - app.camera[0],
                                 arrow.y - app.camera[1], 8, 8)
        self.arrows.append(arrow)

    def update_arrows(self, app):
        #move arrows
        for i, a in enumerate(self.arrows):
            a.x += a.dx * app.deltaTime
            a.y += a.dy * app.deltaTime
            a.rect.x = a.x - app.camera[0]
            a.rect.y = a.y - app.camera[1]

            #delete arrow if hits player
            if a.rect.colliderect(app.player.rect):
                if a.infected:
                    app.player.get_hurt(app, 15, f"Player was hit by infected arrow for 15 damage.")
                else:
                    app.player.get_hurt(app, 10, f"Player was hit by arrow for 10 damage.")

                del self.arrows[i]
                
            for b in app.map.bushes:
                if a.rect.colliderect(b.rect) and not b.damaged:
                    del self.arrows[i]
                    b.hp -= 100
                    break

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
            self.make_arrow(app, 3 * math.cos(angle),
                3 * math.sin(angle))
            self.make_arrow(app, 3 * math.cos(angle - math.pi / 7),
                3 * math.sin(angle - math.pi / 7))
            self.make_arrow(app, 3 * math.cos(angle + math.pi / 7),
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
                self.make_arrow(app, 10 * math.cos(angle),
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
                    app.player.get_hurt(app, 22, f"Player was hit by infected bullet for 22 damage.")
                else:
                    app.player.get_hurt(app, 26, f"Player was hit by bullet for 26 damage.")

                del self.arrows[i]
                
            for b in app.map.bushes:
                if a.rect.colliderect(b.rect) and not b.damaged:
                    b.hp -= 100
                    if random.random() < 0.000004:
                        del self.arrows[i]
                    break

        #delete oldest round when cap is reached
        if len(self.arrows) > 16:
            del self.arrows[0]
