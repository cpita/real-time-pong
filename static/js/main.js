document.addEventListener('DOMContentLoaded', () => {
    let player_type
    const canvas = document.getElementById('canvas')
    const game_constants = JSON.parse(canvas.dataset.game_constants.replace(/'/g, '"'))
    const ctx = canvas.getContext('2d')

    const pos = {
        player1: 0,
        player2: 0,
        ball: [0, 0],
        update: (newPos) => {
            pos.player1 = newPos.player1
            pos.player2 = newPos.player2
            pos.ball = newPos.ball
        },
    }

    const socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port)

    socket.on('connect', () => {

        socket.emit('registerPlayer', '')

        document.onkeydown = key => {
            if (player_type === 'spect') return
            if (key.keyCode === 38 && pos[player_type] > 0) {
                socket.emit('posUpdate', { 'dir': -1, 'player_type': player_type })
            } else if (key.keyCode === 40 && pos[player_type] < game_constants['CANVAS_HEIGHT'] - game_constants['PADDLE_HEIGHT']) {
                socket.emit('posUpdate', { 'dir': 1, 'player_type': player_type })
            } 
        }
    })

     socket.on('registerResponse', r_player_type => {
         player_type = r_player_type
     })
    
    socket.on('update', (data, points1, points2) => {
        document.querySelector('div').innerHTML = points1 + ':' + points2
        pos.update(data)
        ctx.fillStyle = 'rgb(0, 0, 0)'
        ctx.fillRect(0, 0, game_constants['CANVAS_WIDTH'], game_constants['CANVAS_HEIGHT'])
        ctx.fillStyle = 'rgb(255, 255, 255)'
        ctx.fillRect(game_constants['PADDLE_MARGIN'], pos.player1, game_constants['PADDLE_WIDTH'], game_constants['PADDLE_HEIGHT'])
        ctx.fillRect(game_constants['CANVAS_WIDTH'] - game_constants['PADDLE_WIDTH'] - game_constants['PADDLE_MARGIN'], pos.player2, game_constants['PADDLE_WIDTH'], game_constants['PADDLE_HEIGHT'])
        ctx.beginPath()
        ctx.arc(pos.ball[0], pos.ball[1], game_constants['BALL_RADIUS'], 0, Math.PI * 2)
        ctx.closePath()
        ctx.fill()
    })

    window.addEventListener('beforeunload', () => {
        socket.emit('unRegisterPlayer', player_type)
    })

})