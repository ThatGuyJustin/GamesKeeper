from .utility import BoardUtility

class Board:
    def __init__(self, id:int=0):
        self.id = id
        self.utility = BoardUtility(self)

    def __str__(self, id:int=0):
        statement = ''
        for i, symbol in enumerate(self.utility.get_board_list()):
            statement +=('\n' if (i/3)%1==0 else '') + ['-', 'X', 'O'][symbol]
        return statement

class Game(Board):
    def __init__(self, player_1, player_2):
        self.player_1 = player_1
        self.player_2 = player_2

        player_1.set_board(self)
        player_2.set_board(self)

        super().__init__()

class TerminalGame(Game):
    def run(self):
        flag = True
        while flag:
            print(str(self))
            if not (self.utility.get_empty_indices() and not self.utility.who_won()):
                flag=False
            else:
                player_1_input = self.player_1.get_input()
                if not player_1_input == None:
                    self.utility.set_value(player_1_input, 1)
                player_2_input = self.player_2.get_input()
                if not player_2_input == None:
                    self.utility.set_value(player_2_input, 2)
        if not self.utility.get_empty_indices():
            print('It was a draw!')
        else:
            print('Player ' + str(self.utility.who_won()) + ' won.')

class DiscordGame(Game):
    def __init__(self, player_1, player_2, channel):
        self.channel = channel
        self.buttons = '1⃣2⃣3⃣🅰🅱🇨'
        self.emoji = ["<:TicTacToeBlank:594234825716531250>", "<:TicTacToeX:594234825586507777>", "<:TicTacToeO:594234826190749705>", "<:blank:594342155565400114>"]
        super().__init__(player_1, player_2)

    def __str__(self):
        board_list = self.utility.get_board_list()
        return f'''{self.buttons[0]}{emoji[board_list[0]]}{emoji[board_list[1]]}{emoji[board_list[2]]}
{self.buttons[1]}{emoji[board_list[3]]}{emoji[board_list[4]]}{emoji[board_list[5]]}
{self.buttons[2]}{emoji[board_list[6]]}{emoji[board_list[7]]}{emoji[board_list[8]]}
{emoji[3]}{self.buttons[3]}{self.buttons[4]}{self.buttons[5]}'''


    async def run(self):
        self.message = await ctx.send('Setting up Tic Tac Toe.')
        flag = True
        while flag:

            if not (self.utility.get_empty_indices() and not self.utility.who_won()):
                flag=False
            else:
                player_1_input = self.player_1.get_input()
                if not player_1_input == None:
                    self.utility.set_value(player_1_input, 1)
                player_2_input = self.player_2.get_input()
                if not player_2_input == None:
                    self.utility.set_value(player_2_input, 2)
        if not self.utility.get_empty_indices():
            print('It was a draw!')
        else:
            print('Player ' + str(self.utility.who_won()) + ' won.')