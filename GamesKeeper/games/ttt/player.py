from .board import Board
from .board import DiscordGame
from .utility import Utility

import random

async def get_input(self, check):
        done, pending = await asyncio.wait([
                    self.client.wait_for('reaction_remove', check=check),
                    self.client.wait_for('reaction_add', check=check)
                ], return_when=asyncio.FIRST_COMPLETED, timeout=60)

        if done:
            stuff = done.pop().result()

            for future in pending:
                future.cancel()

            return(str(stuff[0].emoji))
        else:
            return('timeout')

MODES = {
    'win': {
        'win':   1,
        'tie':   0,
        'lose': -1
    },
    'lose': {
        'lose':  1,
        'tie':   0,
        'win':  -1
    },
    'tie': {
        'tie':   1,
        'lose': -1,
        'win':  -1
    }
}

class GamePlayer:
    def __init__(self, id:int):
        self.id = id

    def set_board(self, board:Board):
        self.board = board

    def test_input(self, player_input):
        return True if self.board.utility.get_index(player_input) else False

class TerminalPlayer(GamePlayer):
    def get_input(self, failed_previously:bool=False) -> int:
        if self.board.utility.get_empty_indices():
            try:
                player_input = int(input(f"Player {self.id}: Choose tile. "))
                if not (0 <= player_input and player_input <= 8):
                    print(f"Player {self.id}: Please keep your input within the range of 0<=n<=9. Try again.")
                    return self.get_input(failed_previously=True)
            except:
                print(f"Player {self.id}: Please do not input non-integers. Try again.")
                return self.get_input(failed_previously=True)
            if self.test_input(player_input):
                print(f"Player {self.id}: There is already a tile there. Try again.")
                return self.get_input(failed_previously=True)
            return player_input
        else:
            return None

class DiscordPlayer(GamePlayer):
    def __init__(self, id:int, player):
        self.member = player
        self.name = str(player)
        super().__init__(id)

    async def get_input(self):
        pass

class AIPlayer(GamePlayer):
    def __init__(self, id:int, difficulty:float, mode:str='win'):
        self.difficulty = difficulty
        self.states = MODES[mode]

        super().__init__(id)

    def minimax(self):
        def minimax(current_board, my_turn=True):
            if Utility.who_won(current_board) == 3-self.id:
                return self.states['lose']
            elif Utility.who_won(current_board) == self.id:
                return self.states['win']
            elif not Utility.get_board_list(current_board):
                return self.states['tie']

            if my_turn:
                maximum = 0
                flag = True
                for i in Utility.get_empty_indices(current_board):
                    tmp = Utility.set_value(current_board, i, self.id)
                    score = minimax(tmp, my_turn=False)
                    if flag or score > maximum:
                        maximum = score
                        flag = False

                return maximum
            else:
                minimum = 0
                flag = True
                for i in Utility.get_empty_indices(current_board):
                    tmp = Utility.set_value(current_board, i, 3 - self.id)
                    score = minimax(tmp, my_turn=True)
                    if flag or score < minimum:
                        minimum = score
                        flag = False

                return minimum

        places = [[i] for i in Utility.get_empty_indices(self.board.id)]

        best_index = 0
        flag = True

        for i, loc in enumerate(places):
            tmp = Utility.set_value(self.board.id, loc[0], self.id)
            loc.append(minimax(tmp, my_turn=False))
            if flag or places[best_index][1] < loc[1]:
                best_index = i
                flag = False
        return places,best_index

    def get_input(self) -> int:
        try:
            places, best_index = self.minimax()
        except:
            return None
        try:
            big_brain = []
            small_brain = []

            for i in places:
                if i[1] == places[best_index][1]:
                    big_brain.append(i[0])
                else:
                    small_brain.append(i[0])

            return random.choice(big_brain) if random.random() <= self.difficulty else random.choice(small_brain)
        except:
            return None

class DiscordAIPlayer(AIPlayer):
    def __init__(self, id:int, difficulty:float, mode:str='win'):
        self.name = 'AI'

        super().__init__(id, difficulty, mode)

