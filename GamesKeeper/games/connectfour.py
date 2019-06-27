# -*- coding: utf-8 -*-
from random import randrange
from disco.types.channel import ChannelType
from disco.types.permissions import Permissions
from GamesKeeper.models.guild import Guild
import gevent
DEFAULT_BOARD = """| {blank_space} | {blank_space} | {blank_space} | {blank_space} | {blank_space} | {blank_space} | {blank_space} |
---------------------------------------------
| {spaces[0][0]} | {spaces[0][1]} | {spaces[0][2]} | {spaces[0][3]} | {spaces[0][4]} | {spaces[0][5]} | {spaces[0][6]} |
| {spaces[1][0]} | {spaces[1][1]} | {spaces[1][2]} | {spaces[1][3]} | {spaces[1][4]} | {spaces[1][5]} | {spaces[1][6]} |
| {spaces[2][0]} | {spaces[2][1]} | {spaces[2][2]} | {spaces[2][3]} | {spaces[2][4]} | {spaces[2][5]} | {spaces[2][6]} |
| {spaces[3][0]} | {spaces[3][1]} | {spaces[3][2]} | {spaces[3][3]} | {spaces[3][4]} | {spaces[3][5]} | {spaces[3][6]} |
| {spaces[4][0]} | {spaces[4][1]} | {spaces[4][2]} | {spaces[4][3]} | {spaces[4][4]} | {spaces[4][5]} | {spaces[4][6]} |
| {spaces[5][0]} | {spaces[5][1]} | {spaces[5][2]} | {spaces[5][3]} | {spaces[5][4]} | {spaces[5][5]} | {spaces[5][6]} |
---------------------------------------------
| :regional_indicator_a: | :regional_indicator_b: | :regional_indicator_c: | :regional_indicator_d: | :regional_indicator_e: | :regional_indicator_f: | :regional_indicator_g: |

:red_circle: = `{red_player}` {red_status}
:large_blue_circle: = `{blue_player}` {blue_status}
{endgame_stuff}
"""

class Connect4():

    def __init__(self, event, players):
        self.start_event = event
        self.guild = event.guild
        self.who_started = event.author
        self.blue_player = None
        self.red_player = None
        self.current_turn = None
        self.turns = 0
        self.players = self.sort_players(players)
        self.game_channel = self.create_channel(self.players)
        self.game_board = Connect4Board(self.blue_player, self.red_player, self.game_channel)
        self.selected = None
        self.game_over = False
        self.winner = None
    
    def sort_players(self, players):
        number = randrange(10)
        if number % 2 == 0:
            self.blue_player = Connect4Player(players[0], "blue")
            self.red_player = Connect4Player(players[1], "red")
            self.current_turn = self.blue_player
        else:
            self.blue_player = Connect4Player(players[1], "blue")
            self.red_player = Connect4Player(players[0], "red")
            self.current_turn = self.blue_player
        
        return [players[0].id, players[1].id]

    def create_channel(self, players):
        guild_obj = Guild.using_id(self.guild.id)
        
        channel_name = "{}_vs_{}".format(self.red_player.user_object, self.blue_player.user_object)
        channel_name = channel_name.replace('#', '-')
        channel_name = channel_name.replace('#', '-')
        channel = self.guild.create_channel(parent_id=guild_obj.games_category, name=channel_name, channel_type=ChannelType.GUILD_TEXT)
        
        self.update_permissions(channel, guild_obj)
        return channel

    def update_permissions(self, channel, guild_obj):
        for x in self.guild.roles:
            role = self.guild.roles.get(x)
            if str(role) == '@everyone':
                ow = channel.create_overwrite(entity=role)
                ow.deny.add(Permissions.SEND_MESSAGES)
                ow.deny.add(Permissions.READ_MESSAGES)
                ow.deny.add(Permissions.MANAGE_MESSAGES)
                ow.deny.add(1 << 6) #Add Reactions
                ow.save()
        
        if len(guild_obj.spectator_roles) > 0:
            for spec in guild_obj.spectator_roles:
                role = self.guild.roles.get(spec)
                ow = channel.create_overwrite(entity=role)
                ow.allow.add(Permissions.READ_MESSAGES)
                ow.save()
        
        for player in self.players:
            member = self.guild.get_member(player)
            ow = channel.create_overwrite(entity=member)
            ow.allow.add(Permissions.READ_MESSAGES)
            ow.save()
    
    def handle_turn(self, event):
        if event.user_id != self.current_turn.id or event.message_id != self.game_board.game_message.id:
            return False
        if self.game_over:
            return True

        place = None
        if event.emoji.name != '✅':
            switcher = { 
                '\U0001f1e6': 'a',
                '\U0001f1e7': 'b',
                '\U0001f1e8': 'c',
                '\U0001f1e9': 'd',
                '\U0001f1ea': 'e',
                '\U0001f1eb': 'f',
                '\U0001f1ec': 'g'
            }
            place = switcher.get(event.emoji.name, None)
            self.selected = place
        
        if self.selected == None or self.game_board.spots[self.selected][0].taken:
            return False

        isOver = False
        if event.emoji.name == '✅':
            player = self.current_turn
            spot = self.game_board.update_space(self.selected, player, self.turns)
            updated_1 = spot['updated']
            updated_2 = self.game_board.update_board()
            if updated_1 and updated_2:
                self.turns = self.turns + 1
                is_game_over = self.check_wins(event.user_id)
                if is_game_over:
                    isOver = True
                    self.end_game()
                self.clean_reactions()
                self.selected = None
                is_tie = self.check_tie()
                if is_tie:
                    self.winner = 'draw'
                    return True
                if spot['next_turn'] == 'blue':
                    self.current_turn = self.blue_player
                else:
                    self.current_turn = self.red_player
            else:
                self.end_game()
        
        return isOver
    
    def check_tie(self):
        is_tie = True
        for row in range(len(self.game_board.spaces)):
            for spot in range(len(self.game_board.spaces[row])):
                spot_thing = self.game_board.spaces[row][spot]
                if spot_thing.owner_id is not None:
                    continue
                else:
                    is_tie = False
                    break
        return is_tie

    def clean_reactions(self):
        switcher = { 
                'a': '\U0001f1e6',
                'b': '\U0001f1e7',
                'c': '\U0001f1e8',
                'd': '\U0001f1e9',
                'e': '\U0001f1ea',
                'f': '\U0001f1eb',
                'g': '\U0001f1ec'
            }
        emote = switcher.get(self.selected, None)
        emotes = [
            emote,
            "✅"
        ]
        def rvm_reaction(emoji):
            gevent.sleep(1)
            self.game_board.game_message.delete_reaction(emoji, self.current_turn.id)
        
        for x in emotes:
            gevent.spawn(rvm_reaction(x))

    def end_game(self):
        self.game_channel.send_message('Game ended, the winner is **{}**!'.format(self.guild.get_member(self.winner).user))
        self.game_over = True
        return True
    
    def check_wins(self, player_id):
        #Check every row for a win
        is_over = False
        current_count = 0
        for row in range(len(self.game_board.spaces)):
            for spot in range(len(self.game_board.spaces[row])):
                spot_thing = self.game_board.spaces[row][spot] 
                if spot_thing.owner_id == player_id:
                    current_count = current_count + 1
                else:
                    current_count = 0
                if current_count == 4:
                    self.winner = player_id
                    break

        if current_count >= 4:
            is_over = True
            return is_over
        
        #Check every column for a win
        current_count = 0
        for spot in reversed(list(self.game_board.spots[self.game_board.last_play['col']].values())):
            if spot.owner_id == player_id:
                current_count = current_count + 1
            else:
                current_count = 0
            
            if current_count == 4:
                self.winner = player_id
                break

        #Checks all diagonals for a win.
        found = self.check_diag(self.game_board.last_play, player_id)

        if found:
            self.winner = player_id
            is_over = True

        if current_count >= 4:
            is_over = True
        
        return is_over

    def check_diag(self, pos, player_id):
        # board_list = self.game_board.spaces
        spot = self.game_board.spots[pos['col']][pos['row']]
        index = self.index_2d(spot)
        row = index[0]
        col = index[1]
        # starting_point = board_list[row][col]
        left_check = self.diag_left(row, col, player_id)
        right_check = self.diag_right(row, col, player_id)
        if left_check or right_check:
            return True

        return False
    
    def index_2d(self, v):
        board_list = self.game_board.spaces
        for i, x in enumerate(board_list):
            if v in x:
                return [i, x.index(v)]

    def diag_left(self, row, col, player_id):
        next_check_row = row
        next_check_col = col
        count = 0
        # check by going up first
        for x in range(10):
            check = self.game_board.spaces[next_check_row][next_check_col]
            if check.owner_id == player_id:
                count = count + 1
                ur = False
                uc = False
                if 0 < next_check_row < 5:
                    next_check_row = next_check_row - 1
                    ur = True
                if 0 < next_check_col < 6:
                    next_check_col = next_check_col - 1
                    uc = True
                if ur or uc:
                    continue
                else:
                    break
            else:
                break
        
        next_check_row = row
        next_check_col = col
        if 0 < next_check_row < 5:
            next_check_row = next_check_row + 1
        if 0 < next_check_col < 6:
            next_check_col = next_check_col + 1
        # Now check going the oppsite direction
        for x in range(10):
            check = self.game_board.spaces[next_check_row][next_check_col]
            if check.owner_id == player_id:
                count = count + 1
                ur = False
                uc = False
                if 0 < next_check_row < 5:
                    next_check_row = next_check_row + 1
                    ur = True
                if 0 < next_check_col < 6:
                    next_check_col = next_check_col + 1
                    uc = True
                if ur or uc:
                    continue
                else:
                    break
            else:
                break

        if count >= 4:
            return True
        else:
            return False
    
    def diag_right(self, row, col, player_id):
        next_check_row = row
        next_check_col = col
        count = 0
        # check by going up first
        for x in range(10):
            check = self.game_board.spaces[next_check_row][next_check_col]
            if check.owner_id == player_id:
                count = count + 1
                ur = False
                uc = False
                if 0 < next_check_row < 5:
                    next_check_row = next_check_row - 1
                    ur = True
                if 0 < next_check_col < 6:
                    next_check_col = next_check_col + 1
                    uc = True
                if ur or uc:
                    continue
                else:
                    break
            else:
                break
        
        next_check_row = row
        next_check_col = col
        if 0 < next_check_row < 5:
            next_check_row = next_check_row + 1
        if 0 < next_check_col < 6:
            next_check_col = next_check_col - 1
        # Now check going the oppsite direction
        for x in range(10):
            check = self.game_board.spaces[next_check_row][next_check_col]
            if check.owner_id == player_id:
                count = count + 1
                ur = False
                uc = False
                if 0 < next_check_row < 5:
                    next_check_row = next_check_row + 1
                    ur = True
                if 0 < next_check_col < 6:
                    next_check_col = next_check_col - 1
                    uc = True
                if ur or uc:
                    continue
                else:
                    break
            else:
                break
        
        if count >= 4:
            return True
        else:
            return False


class Connect4Player():

    def __init__(self, player, color):
        self.color = color
        self.user_object = player
        self.last_turn = None
        self.turns = 0
        self.id = player.id
    

    def __str__(self):
        return '{username}#{discrim}'.format(username=self.user_object.username, discrim=self.user_object.discriminator)


class Connect4Spot():

    colors = {
        "blue": ":large_blue_circle:",
        "red": ":red_circle:",
        "blank": ":black_circle:"
    }

    def __init__(self):
        self.color = ":black_circle:"
        self.taken = False
        self.owner_id = None
        self.turn_placed = 0

    def __str__(self):
        return self.color

    def update(self, color, turn):
        self.color = self.colors.get(color)
        self.turn = turn

class Connect4Board():
    def __init__(self, blue, red, channel):

        self.spots = {
            "a": {
                0: Connect4Spot(),
                1: Connect4Spot(),
                2: Connect4Spot(),
                3: Connect4Spot(),
                4: Connect4Spot(),
                5: Connect4Spot()
            },
            "b": {
                0: Connect4Spot(),
                1: Connect4Spot(),
                2: Connect4Spot(),
                3: Connect4Spot(),
                4: Connect4Spot(),
                5: Connect4Spot()
            },
            "c": {
                0: Connect4Spot(),
                1: Connect4Spot(),
                2: Connect4Spot(),
                3: Connect4Spot(),
                4: Connect4Spot(),
                5: Connect4Spot()
            },
            "d": {
                0: Connect4Spot(),
                1: Connect4Spot(),
                2: Connect4Spot(),
                3: Connect4Spot(),
                4: Connect4Spot(),
                5: Connect4Spot()
            },
            "e": {
                0: Connect4Spot(),
                1: Connect4Spot(),
                2: Connect4Spot(),
                3: Connect4Spot(),
                4: Connect4Spot(),
                5: Connect4Spot()
            },
            "f": {
                0: Connect4Spot(),
                1: Connect4Spot(),
                2: Connect4Spot(),
                3: Connect4Spot(),
                4: Connect4Spot(),
                5: Connect4Spot()
            },
            "g": {
                0: Connect4Spot(),
                1: Connect4Spot(),
                2: Connect4Spot(),
                3: Connect4Spot(),
                4: Connect4Spot(),
                5: Connect4Spot()
            }
        }
        
        #Notes:
        #spaces[ROW][COL]
        self.spaces = [[self.spots["a"][0], self.spots["b"][0], self.spots["c"][0], self.spots["d"][0], self.spots["e"][0], self.spots["f"][0], self.spots["g"][0]], #0
                [self.spots["a"][1], self.spots["b"][1], self.spots["c"][1], self.spots["d"][1], self.spots["e"][1], self.spots["f"][1], self.spots["g"][1]], #1
                [self.spots["a"][2], self.spots["b"][2], self.spots["c"][2], self.spots["d"][2], self.spots["e"][2], self.spots["f"][2], self.spots["g"][2]], #2
                [self.spots["a"][3], self.spots["b"][3], self.spots["c"][3], self.spots["d"][3], self.spots["e"][3], self.spots["f"][3], self.spots["g"][3]], #3
                [self.spots["a"][4], self.spots["b"][4], self.spots["c"][4], self.spots["d"][4], self.spots["e"][4], self.spots["f"][4], self.spots["g"][4]], #4
                [self.spots["a"][5], self.spots["b"][5], self.spots["c"][5], self.spots["d"][5], self.spots["e"][5], self.spots["f"][5], self.spots["g"][5]]] #5
        self.game_channel = channel
        self.blue_player = blue
        self.red_player = red
        self.blue_status = "*Selecting...*"
        self.red_status = ""
        self.endgame_stuff = ""
        self.game_message = self.send_message(self.game_channel)
        # Last thing played
        self.last_play = {
            'row': None,
            'col': None 
        }

    def send_message(self, channel):
        msg = channel.send_message(str(self))
        #A B C D E F G
        emotes = [
            "\U0001f1e6",
            "\U0001f1e7",
            "\U0001f1e8",
            "\U0001f1e9",
            "\U0001f1ea",
            "\U0001f1eb",
            "\U0001f1ec",
            "✅"
        ]
        def add_reaction(emoji):
            gevent.sleep(1)
            msg.add_reaction(emoji)
        
        for x in emotes:
            gevent.spawn(add_reaction(x))
        
        return msg

    def update_board(self):
        try:
            self.game_message.edit(str(self))
            return True
        except:
            return False

    def update_space(self, col, player, turnCount):
        current_index = 5
        for x in reversed(list(self.spots[col].values())):
            if x.taken:
                current_index = current_index - 1
                continue
            else:
                x.color = x.colors[player.color]
                x.taken = True
                x.turn_placed = turnCount
                x.owner_id = player.user_object.id
                if player.color == "blue":
                    self.blue_status = ""
                    self.red_status = "*Selecting...*"
                elif player.color == "red":
                    self.red_status = ""
                    self.blue_status = "*Selecting...*"
                break
        self.last_play = {
            'row': current_index,
            'col': col
        }
        return {
            'updated': True,
            'next_turn': 'red' if player.color == 'blue' else 'blue' 
        }
    
    def __str__(self):
        return DEFAULT_BOARD.format(
            spaces=self.spaces, 
            blank_space=":black_circle:", 
            red_player=self.red_player,
            red_status=self.red_status,
            blue_player=self.blue_player, 
            blue_status=self.blue_status,
            endgame_stuff=self.endgame_stuff
        )