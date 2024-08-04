

class GameRoom:
    def __init__(self, room_name):
        self.room_name = room_name
        self.players = {}
        self.actions = {
        }

    def add_player(self, player_id, player_name):
        self.players[player_id] = player_name
        print(f"Player {player_name} has joined the room.")

    def remove_player(self, player_id):
        player_name = self.players.pop(player_id, None)
        if player_name:
            print(f"Player {player_name} has left the room.")
        else:
            print("Player not found in the room.")

    def player_action(self, player_id, action, **kwargs):
        if player_id in self.players:
            action_func = self.actions.get(action)
            if action_func:
                action_func(player_id, **kwargs)
            else:
                print(f"Unknown action: {action}")
        else:
            print("Player not in the room.")

    def player_move(self, player_id, direction):
        print(f"Player {self.players[player_id]} moves {direction}")

    def player_attack(self, player_id, target_id):
        if target_id in self.players:
            print(f"Player {self.players[player_id]} attacks {self.players[target_id]}")
        else:
            print("Target player not found in the room.")