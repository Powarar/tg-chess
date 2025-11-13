// static/index.js

// === 1. Получение данных из HTML ===
const roomData = document.getElementById("room-data");
const roomId = roomData.getAttribute("data-room-id");
const username = roomData.getAttribute("data-username");
const userId = roomData.getAttribute("data-user-id");

const statusEl = document.getElementById("status");
let board = null; // Глобальная переменная для объекта Chessboard.js
let playerColor = 'white'; // Цвет, назначенный игроку
let boardState = null; // Объект для хранения состояния игры (шах, очередь хода и т.д.)

// === 2. Настройка WebSocket ===
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const host = window.location.host;

// URL соответствует роутеру FastAPI: /ws/board/{room_id}/{user_id}?username=...
const wsUrl = `${protocol}//${host}/ws/board/${roomId}/${userId}?username=${username}`;
const ws = new WebSocket(wsUrl);

ws.onopen = () => {
    console.log("Соединение установлено");
};

ws.onclose = () => {
    statusEl.textContent = "Соединение закрыто. Перезагрузите страницу.";
    console.log("Соединение закрыто");
};

// === 3. Функция для обработки хода игрока ===
// Вызывается библиотекой Chessboard.js, когда игрок отпускает фигуру.
function onDrop(source, target, piece, newPos, oldPos, orientation) {
    // Проверка, что игрок ходит своим цветом
    // 'w' или 'b' берется из boardState.turn (чей сейчас ход)
    const pieceColor = piece.startsWith('w') ? 'white' : 'black';
    const turnColor = boardState.turn === 'w' ? 'white' : 'black';

    if (playerColor !== turnColor || playerColor !== pieceColor) {
        // Если ходит не его очередь или он пытается ходить чужой фигурой
        return 'snapback'; // Откатить ход
    }
    
    // Формируем ход в формате, который ждет сервер (router_socket.py)
    const move = {
        from: source,
        to: target
        // Примечание: Промоция пешки здесь не обрабатывается, это задача для мидла
    };
    
    // Отправляем ход на сервер в формате JSON
    ws.send(JSON.stringify(move));
    
    // Возвращаем 'snapback'. Фигура вернется на место, пока сервер не подтвердит ход 
    // и не пришлет обновленное состояние (data.type === 'update').
    return 'snapback'; 
}


// === 4. Обработчик сообщений от сервера ===
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'init') {
        // Инициализация: Первое сообщение при подключении
        playerColor = data.color;
        boardState = data; // Сохраняем начальное состояние
        
        const config = {
            draggable: true, // Можно перетаскивать фигуры
            position: data.fen, // Начальная позиция
            orientation: playerColor, // Поворот доски (белые снизу или черные снизу)
            onDrop: onDrop, // Наша функция-обработчик хода
            // Исправление 404 ошибки: указываем путь к изображениям
            pieceTheme: 'https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/img/chesspieces/wikipedia/{piece}.png'
        };
        
        board = Chessboard('myBoard', config); // Инициализируем доску
        updateStatus();
        
    } else if (data.type === 'update') {
        // Обновление: Приходит после каждого легального хода
        if (board) {
            boardState = data; // Обновляем состояние игры
            board.position(data.fen); // Обновляем положение фигур
        }
        updateStatus();
        
    } else if (data.type === 'error') {
        // Ошибка: Приходит, если игрок сделал нелегальный ход
        alert(`Ошибка: ${data.message}`);
        // Фигура уже вернулась благодаря 'snapback' в onDrop
    }
};

// === 5. Вспомогательная функция для обновления статуса ===
function updateStatus() {
    if (!boardState) return;

    let status = `Вы играете за: ${playerColor}. Ход: ${boardState.turn === 'w' ? 'Белых' : 'Черных'}.`;

    if (boardState.is_game_over) {
        status = 'Игра окончена! ';
        if (boardState.is_checkmate) {
            status += `Победа ${boardState.turn === 'w' ? 'Черных' : 'Белых'} (Мат).`;
        } else if (boardState.is_stalemate) {
            status += 'Пат (Ничья).';
        } else if (boardState.is_draw) {
            status += 'Ничья.';
        }
    } else if (boardState.is_check) {
        status += ` ${boardState.turn === 'w' ? 'Белым' : 'Черным'} Шах!`;
    }

    statusEl.textContent = status;
}