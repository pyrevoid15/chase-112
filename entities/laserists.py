import pygame
import random, math
from entities.entity import Entity
from utilities import *

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
        
        self.rect = pygame.Rect(self.startx, self.starty,
                                self.endx - self.startx, self.endy - self.starty)

    def update(self, app, dtheta=0, power=50, lengthen=True): 
        self.angle += dtheta
        self.timer += 1
        
        if lengthen:
            self.length += self.speed * app.deltaTime
            if not self.anchored:
                self.startx += math.cos(self.angle) * self.speed
                self.starty += math.sin(self.angle) * self.speed
                self.endx += self.speed + math.cos(self.angle)
                self.endy += self.speed + math.sin(self.angle)
            else:
                self.endx = self.startx + math.cos(self.angle) * self.length
                self.endy = self.starty + math.sin(self.angle) * self.length
        else:
            self.endx = self.startx + math.cos(self.angle) * self.length
            self.endy = self.starty + math.sin(self.angle) * self.length

        if self.timer % 70:
            self.switch = not self.switch
            
        self.rect = pygame.Rect(self.startx - app.camera[0], self.starty - app.camera[1],
                                self.endx - self.startx, self.endy - self.starty)


    def laserX_line(self, start, end):
        return lineXline(self.rect.topleft, self.rect.bottomright, start, end)
    
    def laserX_rect(self, rect):
        if self.laserX_line(rect.topleft, rect.topright) or\
             self.laserX_line(rect.topleft, rect.bottomleft) or\
             self.laserX_line(rect.topright, rect.bottomright) or\
             self.laserX_line(rect.bottomleft, rect.bottomright):
            return True
        return False

    def render(self, canvas):
        canvas.create_line(self.rect.x, self.rect.y, self.rect.right, self.rect.bottom,
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
                
        for b in app.map.bushes:
            if not b.damaged and self.lance.laserX_rect(b.rect):
                b.hp -= 500
                self.mode = 'goto'
                self.mode_ticker = 0
                self.goal = [random.randrange(200, 700), random.randrange(200, 700)]
                break

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
        if self.lance.laserX_rect(app.player.rect):
            app.player.get_hurt(app, 35, f"Player was hit by a lancer in {self.mode} for 35 damage.")

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
                  
            blocked = False  
            for b in app.map.bushes:
                if not b.damaged and l.laserX_rect(b.rect):
                    b.hp -= 4.5
                    blocked = True
                    
                    #cut laser short
                    d = math.sqrt(pow(l.startx - b.pos[0],2) +\
                        pow(l.starty - b.pos[1],2))
                    if d < l.length:
                        l.length = d
                        
                    break
                    
            l.update(app, lengthen=(not blocked))
                
            self.e_vel[0] -= math.cos(l.angle) / 3
            self.e_vel[1] -= math.sin(l.angle) / 3
            
            if l.laserX_rect(app.player.rect):
                app.player.get_hurt(app, 14, f"Player was hit by laser for 14 damage.")
                

    def render(self, canvas):
        for l in self.lasers:
            l.render(canvas)
        if self.laser_countdown % 3 == 0 and self.laser_countdown < 50 and self.laser_countdown >= 0:
            canvas.create_rectangle(self.rect.x, self.rect.y,
             self.rect.right, self.rect.bottom, outline="#ffffff")
        else:
            super().render(canvas)

