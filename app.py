from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import time, threading, logging
from math import sin, cos, radians

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

socketio = SocketIO(app)

#Define game constants dict
game_constants = {
    "CANVAS_WIDTH" : 600,
    "CANVAS_HEIGHT" : 600,
    "BALL_VELOCITY" : 15,
    "PLAYER_VELOCITY" : 15,
    "MAX_BOUNCE_ANGLE" : 75,
    "PADDLE_HEIGHT" : 100,
    "PADDLE_WIDTH" : 20,
    "PADDLE_MARGIN" : 10,
    "BALL_RADIUS" : 10
}
#Define game positions and player information dicts
pos = {
    'player1': (game_constants['CANVAS_HEIGHT'] - game_constants['PADDLE_HEIGHT'])/2,
    'player2': (game_constants['CANVAS_HEIGHT'] - game_constants['PADDLE_HEIGHT'])/2,
    'ball': [game_constants['CANVAS_WIDTH']/2, game_constants['CANVAS_HEIGHT']/2],
    'ballVect': [1, 0]
}
players = {
    'player1': {
        'name': None,
        'points': 0
    }, 'player2': {
        'name': None,
        'points': 0
    }
}


@app.route('/')
def index():
    return render_template('index.html', game_constants = game_constants, points1 = players['player1']['points'], points2 = players['player2']['points'])

#Assigns to each client that connects one of the following: player1, player2 or spectator
@socketio.on('registerPlayer')
def registerPlayer(player_name):
    player_type = 'spect'
    if players['player1']['name'] is None:
        players['player1']['name'] = player_name
        player_type = 'player1'
    elif players['player2']['name'] is None:
        players['player2']['name'] = player_name
        player_type = 'player2'
    emit('registerResponse', player_type)
    
#Stops the game if one of the players disconnects
@socketio.on('unRegisterPlayer')
def unRegisterPlayer(player_type):
    if player_type == 'spect':
        return
    players[player_type]['name'] = None

#Listens for player movements and updates their position
@socketio.on('posUpdate')
def posUpdate(data):
    direction = data['dir']
    player_type = data['player_type']
    if player_type == 'player1':
        pos['player1'] = pos['player1'] + game_constants['PLAYER_VELOCITY'] * int(direction)
    elif player_type == 'player2':
        pos['player2'] = pos['player2'] + game_constants['PLAYER_VELOCITY'] * int(direction)

#Main game loop
def gameLoop():
    if players['player1']['name'] is not None and players['player2']['name'] is not None:
        #Check if player 1 wins
        if pos['ball'][0] > game_constants['CANVAS_WIDTH']:
            players['player1']['points'] += 1
            pos['ball'] = [300, 300]
            pos['ballVect'] = [-1, 0]
        #Check if player 2 wins
        elif pos['ball'][0] < 0:
            players['player2']['points'] += 1
            pos['ball'] = [300, 300]
            pos['ballVect'] = [1, 0]
        #Else move the ball
        else:
            newVect = newBallVect()
            #Update ball's velocity vector if a collision has been detected
            if newVect is not None:
                pos['ballVect'] = newVect
            #Update ball's position
            pos['ball'][0], pos['ball'][1] = pos['ball'][0] + \
                pos['ballVect'][0] * game_constants['BALL_VELOCITY'], pos['ball'][1] + \
                pos['ballVect'][1] * game_constants['BALL_VELOCITY']

    #Send information to all connected users and start again
    socketio.emit(
        'update', (pos, players['player1']['points'], players['player2']['points']))
    threading.Timer(1/30, gameLoop).start()

def newBallVect():
    #Check collision with player 1
    if pos['ball'][0] - game_constants['BALL_RADIUS'] <= 30 and pos['ball'][1] >= pos['player1'] and pos['ball'][1] <= pos['player1'] + game_constants['PADDLE_HEIGHT']:
        normDist = (pos['ball'][1] - pos['player1'] -
                    game_constants['PADDLE_HEIGHT']/2) / (game_constants['PADDLE_HEIGHT']/2)
        return [cos(radians(normDist * game_constants['MAX_BOUNCE_ANGLE'])), sin(radians(normDist * game_constants['MAX_BOUNCE_ANGLE']))]
    #Check collision with player 2
    elif pos['ball'][0] + game_constants['BALL_RADIUS'] >= game_constants['CANVAS_WIDTH'] - 30 and pos['ball'][1] >= pos['player2'] and pos['ball'][1] <= pos['player2'] + game_constants['PADDLE_HEIGHT']:
        normDist = (pos['ball'][1] - pos['player2'] -
                    game_constants['PADDLE_HEIGHT']/2) / (game_constants['PADDLE_HEIGHT']/2)
        return [-1 * cos(radians(normDist * game_constants['MAX_BOUNCE_ANGLE'])), sin(radians(normDist * game_constants['MAX_BOUNCE_ANGLE']))]
    #Check collision with upper and lower walls
    elif pos['ball'][1] - game_constants['BALL_RADIUS'] <= 0 or pos['ball'][1] + game_constants['BALL_RADIUS'] > game_constants['CANVAS_HEIGHT']:
        return [pos['ballVect'][0], -1 * pos['ballVect'][1]]


gameLoop()
