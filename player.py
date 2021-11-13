import entities.entity as ent

class Player(ent.Entity):
    def __init__(self, app) -> None:
        super().__init__(100, 100)

        self.app = app
        self.input = [False] * 4
        self.is_dead = False
        self.color = "#ff0000"
        self.pausing = False

    def init_events(self, event):
        if event.key == "Left":
            self.input[0] = True
        elif event.key == "Right":
            self.input[1] = True
        elif event.key == "Up":
            self.input[2] = True
        elif event.key == "Down":
            self.input[3] = True
        elif event.key == "Escape":
            self.pausing = True

    def cancel_events(self, event):
        if event.key == "Left":
            self.input[0] = False
        elif event.key == "Right":
            self.input[1] = False
        elif event.key == "Up":
            self.input[2] = False
        elif event.key == "Down":
            self.input[3] = False

    def update(self, app):
        if self.input[0] and self.input[1]:
            self.i_vel[0] = 0
        elif self.input[0]:
            self.i_vel[0] = max(self.i_vel[0] - 0.3, -1.3)
        elif self.input[1]:
            self.i_vel[0] = min(self.i_vel[0] + 0.3, 1.3)
        else:
            self.i_vel[0] /= 3
            if abs(self.i_vel[0]) < 0.2:
                self.i_vel[0] = 0

        if self.input[2] and self.input[3]: 
            self.i_vel[1] = 0
        elif self.input[2]:
            self.i_vel[1] = max(self.i_vel[1] - 0.3, -1.3)
        elif self.input[3]:
            self.i_vel[1] = min(self.i_vel[1] + 0.3, 1.3)
        else:
            self.i_vel[1] /= 3
            if abs(self.i_vel[1]) < 0.2:
                self.i_vel[1] = 0

        self.update_pos(app)
        self.update_hp()
        
        if self.pausing:
            self.pausing = False
            app.mode = 'pause'

    def update_hp(self):
        if self.hp < 100:
            self.hp += 1 / 99
        else:
            self.hp = 100
        if self.invincibility > -3:
            self.invincibility -= 1

    def get_hurt(self, app, power, message=''):
        if self.invincibility <= 0:
            self.hp -= power
            self.invincibility = min(power, 70) * 5
            if self.hp < 0:
                self.is_dead = True
            
            if message != '':
                #print(message)
                app.message = message
