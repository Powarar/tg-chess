from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import chess
import json

router = APIRouter(prefix='/ws/board')

class GameManager:
    def __init__(self):
        # Хранение активных соединений в виде {room_id: {user_id: WebSocket}}
        self.active_connections: dict[int, dict[int, WebSocket]] = {}
        # Хранение состояния досок: {room_id: chess.Board}
        self.game_states: dict[int, chess.Board] = {}

    async def connect(self, websocket: WebSocket, room_id: int, user_id: int):
        await websocket.accept()



        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
            self.game_states[room_id] = chess.Board()
            player_color = "white"
        else:
            player_color = "black"
        
        self.active_connections[room_id][user_id] = websocket

        board_fen = self.game_states[room_id].fen()
        await websocket.send_json({
            "type": "init",
            "fen": board_fen,
            "color": player_color

        })

    def disconnect(self, room_id: int, user_id: int):
        """
        Закрывает соединение и удаляет его из списка активных подключений.
        Если в комнате больше нет пользователей, удаляет комнату.
        """
        if room_id in self.active_connections and user_id in self.active_connections[room_id]:
            del self.active_connections[room_id][user_id]
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast_state(self, room_id: int):
            """
            Рассылает всем в комнате актуальное состояние доски.
            """
            if room_id in self.game_states:
                board = self.game_states[room_id]
                board_fen = board.fen()
                is_game_over = board.is_game_over()
                
                message = {
                    "type": "update",
                    "fen": board_fen,
                    "is_game_over": is_game_over,
                    "turn": "white" if board.turn == chess.WHITE else "black"
                }
                
                for connection in self.active_connections[room_id].values():
                    await connection.send_json(message)

manager = GameManager()

@router.websocket("/{room_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int, user_id: int, username: str):
   
    await manager.connect(websocket, room_id, user_id)
    # await manager.broadcast_state(f"{username} (ID: {user_id}) присоединился к игре.", room_id, user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            move_data = json.loads(data)

            board = manager.game_states.get(room_id)
            if not board:
                continue
            try:
                move_uci = f"{move_data['from']}{move_data['to']}"
                move = chess.Move.from_uci(move_uci)
                
                # 4. Проверяем, легален ли ход
                if move in board.legal_moves:
                    board.push(move) # Делаем ход
                    # 5. Рассылаем новое состояние всем
                    await manager.broadcast_state(room_id)
                else:
                    # Ход нелегальный, сообщаем только отправителю
                    await websocket.send_json({"type": "error", "message": "Неверный ход"})
            
            except (ValueError, KeyError):
                # Ошибка формата (не 'from'/'to' или не UCI)
                await websocket.send_json({"type": "error", "message": "Неверный формат хода"})
            # await manager.broadcast(f"{username} (ID: {user_id}): {data}", room_id, user_id)
    
    
    
    except WebSocketDisconnect:
        manager.disconnect(room_id, user_id)
        # await manager.broadcast(f"{username} (ID: {user_id}) покинул игру.", room_id, user_id)