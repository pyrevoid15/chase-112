from cmu_112_graphics import *
import player, files, gui
import enemies as entity
import time, math, json, random

from world import Map


def start_keyPressed(app, event):
    app.mode = 'game'

def start_timerFired(app):
    app.ticks += 1
    if app.ticks % 50 == 0:
        app.color = '#' + hex(random.randrange(0, 0xffffff))[2:]
        if len(app.color) != 7:
            app.color = '#969696'
        
def start_redrawAll(app, canvas):
    canvas.create_rectangle(0, 0, app.width, app.height, fill="#000000")
    canvas.create_text(app.width // 2, app.height // 5 * 2, text='CHASE',
                       font="Helvetica 40 bold", fill=app.color)
    canvas.create_text(app.width // 2, app.height // 5 * 2 + 70, text='Press any key.',
                       font="Helvetica 20 bold", fill=app.color)


def pause_keyPressed(app, event):
    if event.key == 'Escape':
        app.mode = 'game'

def pause_redrawAll(app, canvas):
    canvas.create_rectangle(0, 0, app.width, app.height, fill="#000000")
    canvas.create_text(app.width // 2, app.height // 5 * 4, text='Press ESCAPE to unpause.',
                       font="Helvetica 20 bold", fill=app.color)
    

def victory_keyPressed(app, event):
    app.mode = 'start'
    
def victory_timerFired(app, canvas):
    app.ticks += 1
    if app.ticks % 50 == 0:
        app.color = '#' + hex(random.randrange(0, 0xffffff))[2:]
        if len(app.color) != 7:
            app.color = '#969696'

def victory_redrawAll(app, canvas):
    canvas.create_rectangle(0, 0, app.width, app.height, fill="#000000")
    canvas.create_text(app.width // 2, app.height // 2,
                       text='YOU WIN',
                       font="Helvetica 40 bold", fill=app.color)
    canvas.create_text(app.width // 2, app.height // 5 * 4,
                       text='Thank you for playing.',
                       font="Helvetica 18 bold", fill=app.color)

####################################
# Main App
####################################

def appStarted(app):
    print("*")
    app.player = player.Player(app)
    app.entities = []

    app.health_bar = gui.HealthBar()
    app.level = -1
    app.timer = 60 * 100
    app.level_name = "None"
    app.mode = 'start'
    app.color = '#456789'
    app.ticks = 0
    app._root.title("Chase 112")

    #timing
    app.timerDelay = 1
    app.fps = 0
    app.avg_fps = 0
    app.fps_trend = []
    app.now_frame = 1
    app.last_frame = 0
    app.deltaTime = 1
    app.gameOver = False
    app.levelTransition = 100
    app.levelsActive = True #change to false for debug
    
    app.world_left = 0 #do not change
    app.world_top = 0 #do not change
    app.world_right = 700
    app.world_bottom = 700
    
    app.camera = [0, 0]
    app.map = Map(app)

    if app.levelsActive:
        new_level(app)
    else:
        app.entities = [
            entity.Chaser(300, 300),
            entity.Archer(400, 500),
            entity.WeirdArcher(100, 500),
            entity.TChaser(100, 500),
            entity.Trapper(500, 500),
            entity.Rifleman(-100, 300),
            entity.Lancer(300, 400),
            entity.Laserist(800, 300),
            entity.Ghost(200, 700)
        ]

def new_level(app):
    app.level += 1
    try:
        level_data = json.loads(files.File.from_file
        ("levels.json"))[app.level]
    except IndexError:
        app.mode = 'victory'
        
    app.level_name = level_data["name"]
    app.timer = level_data["timer"] * 100
    app.entities.clear()
    if app.level % 5 == 0:
        app.player.hp = min(100, app.player.hp + 50)
    for e in level_data["enemies"]:
        et = e.split(" ")[0]
        if et == "chaser":
            app.entities.append(entity.Chaser(random.randrange(200, 700), random.randrange(200, 700)))
        elif et == "tchaser":
            app.entities.append(entity.TChaser(random.randrange(200, 700), random.randrange(200, 700)))
        elif et == "archer":
            app.entities.append(entity.Archer(random.randrange(200, 700), random.randrange(200, 700)))
        elif et == "warcher":
            app.entities.append(entity.WeirdArcher(random.randrange(200, 700), random.randrange(200, 700)))
        elif et == "vortal":
            app.entities.append(entity.Vortal(random.randrange(200, 700), random.randrange(200, 700)))
        elif et == "trapper":
            app.entities.append(entity.Trapper(random.randrange(200, 700), random.randrange(200, 700)))
        elif et == "rifleman":
            app.entities.append(entity.Rifleman(random.randrange(200, 700), random.randrange(200, 700)))
        elif et == "lancer":
            app.entities.append(entity.Lancer(random.randrange(200, 700), random.randrange(200, 700)))
        elif et == "laserist":
            app.entities.append(entity.Laserist(random.randrange(200, 700), random.randrange(200, 700)))
        elif et == "ghost":
            app.entities.append(entity.Ghost(random.randrange(200, 700), random.randrange(200, 700)))

def game_sizeChanged(app):
    app._root.geometry("700x700")

def game_keyPressed(app, event):
    if app.gameOver:
        appStarted(app)
    else:
        app.player.init_events(event)

def game_keyReleased(app, event):
    if not app.gameOver:
        app.player.cancel_events(event)

def game_timerFired(app):
    if app.levelTransition <= 0:
        # update player and all entities
        app.player.update(app)
        app.health_bar.update(app)
        app.map.update(app)
            
        entity.Trapper.update_explosions(app)
        for e in app.entities:
            e.update(app)
		
        # update camera and manage fps
        manageCamera(app)
        manageTime(app)
        app.timer -= 1 * app.deltaTime

        #change level whe timer reaches zero
        if app.timer <= 0 and app.levelsActive:
            new_level(app)
            app.levelTransition = 100

        #game over
        if app.player.is_dead:
            app.gameOver = True
            app.level = 0
    else:
        app.levelTransition -= 1

def manageTime(app): #to regulate the flow of time for smoothness
    app.last_frame = app.now_frame
    app.now_frame = time.time()
    if app.now_frame - app.last_frame > 0:
        app.fps = 1 / (app.now_frame - app.last_frame)
    else:
        app.fps = 9999999999999999999

    app.fps_trend.append(app.fps)
    if len(app.fps_trend) > 50:
        del app.fps_trend[0]

    app.avg_fps = sum(app.fps_trend) / len(app.fps_trend)
    app.deltaTime = min(100 / app.fps, 99)
    if app.avg_fps > 152:
        app.timerDelay += 1
    elif app.avg_fps < 98:
        app.timerDelay = max(app.timerDelay - 1, 0)

    #print(app.avg_fps)

def manageCamera(app): #to regulate the position of the camera
    app.camera[0] = app.player.pos[0] - app.width // 2
    app.camera[1] = app.player.pos[1] - app.height // 2
    
    if app.camera[0] < 0:
        app.camera[0] = 0
    elif app.camera[0] > app.world_right - app.width:
        app.camera[0] = app.world_right - app.width
        
    if app.camera[1] < 0:
        app.camera[1] = 0
    elif app.camera[1] > app.world_bottom - app.height:
        app.camera[1] = app.world_bottom - app.height
    print(app.camera)

def game_redrawAll(app, canvas):
    if app.gameOver:
        drawGameOver(app, canvas)
    elif app.levelTransition > 0:
        drawLevelTransition(app, canvas)
    else:
        #canvas.create_rectangle(0, 0, app.width, app.height, fill="#00aa00")
        app.map.render_background(app, canvas)
        app.player.render(canvas)
        for e in app.entities:
            e.render(canvas)
        app.map.render_bushes(app, canvas)
        entity.Trapper.render_explosions(app, canvas)
        app.health_bar.render(canvas)

        canvas.create_text(app.width // 2, 35,
            text=f"Level {app.level} - {app.level_name}",
            fill="white", font="Helvetica 10 bold")
        canvas.create_text(app.width - 200, 35,
			text=f"Time: {int(app.timer) // 100}",
            fill="white", font="Helvetica 10 bold")

def drawGameOver(app, canvas):
    canvas.create_rectangle(0, 0, app.width, app.height, fill="black")
    canvas.create_text(app.width // 2, app.height // 2,
     text="DED :(", fill="white", font="Helvetica 44 bold")

def drawLevelTransition(app, canvas):
    canvas.create_rectangle(0, 0, app.width, app.height, fill="blue")
    if app.level == -1:
        canvas.create_text(app.width // 2, app.height // 2,
        text="DEBUG TIME", fill="white", font="Helvetica 44 bold")
    elif app.level == 0:
        canvas.create_text(app.width // 2, app.height // 2,
        text="BEGIN", fill="white", font="Helvetica 44 bold")
    else:
        canvas.create_text(app.width // 2, app.height // 2,
        text="NEXT LEVEL", fill="white", font="Helvetica 44 bold")
        canvas.create_text(app.width // 2, app.height // 2 + 50,
        text=f"Level {app.level} - {app.level_name}",
        fill="white", font="Helvetica 30 bold")
        if app.level % 5 == 0:
            canvas.create_text(app.width // 2, app.height // 2 + 250,
            text=f"Your health was restored.",
            fill="white", font="Helvetica 20 bold")

def main():
    runApp(width=700, height=700)

if __name__ == '__main__':
    main()