import random
from random import randrange
from disco.types.channel import ChannelType
from disco.types.permissions import Permissions
from disco.types.message import MessageEmbed
from GamesKeeper.models.guild import Guild
from GamesKeeper import bot_config
from GamesKeeper import NO_EMOJI_ID, YES_EMOJI_ID, NO_EMOJI, YES_EMOJI
from GamesKeeper.models.games import Games, Users
from math import ceil
import gevent


class Uno():
    def __init__(self, event, players, game_id, spectator_message):
        self.start_event = event
        self.guild = event.guild
        self.who_started = event.author
        self.settings = GameSettings(self)
        self.deck = Deck()
        self.pile = Pile(self.deck.draw())
        self.log_message = ""
        self.current_turn = None
        self.reverse = False
        self.players = self.setup_players(players)
        self.spectator_message = spectator_message
        self.game_id = game_id
        self.game_channels = self.create_channels(self.players)
        self.selected = None
        self.game_over = False
        self.winner = None
        self.generate_messages()
        print(self.settings.rules)

    def generate_messages(self):
        emotes = [
            "\U000025c0",
            "1⃣",
            "2⃣",
            "3⃣",
            "4⃣",
            "5⃣",
            "6⃣",
            "\U000025b6",
            YES_EMOJI,
            NO_EMOJI
        ]

        def add_reaction(msg, emoji):
            gevent.sleep(1.3)
            msg.add_reaction(emoji)

        self.update_messages()
        for player in self.players:
            for x in emotes:
                gevent.spawn(add_reaction(player.message, x))


    def update_messages(self, only_current_player = False):
        player_list = self.print_player_list()
        for player in ([self.current_turn] if only_current_player else self.players):
            embed = MessageEmbed()
            embed.description = self.log_message
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/{}.png?v=1".format(self.pile.top_card.emoji_id))
            embed.set_author(name="Uno", icon_url="https://cdn.discordapp.com/emojis/{}.png?v=1".format(
                bot_config.uno_emojis['uno'].split(':')[1]))
            embed.set_footer(text=player.user,
                             icon_url=player.user.avatar_url)

            embed.add_field(name="Players", value=player_list)
            embed.add_field(name="Pile", value= "<:" + bot_config.uno_emojis['uno'] + ">" + str(self.pile.top_card) + "\n\n")
            if len(self.current_turn.queue) > 0:
                embed.add_field(name="Play?", value= ''.join(str(x) for x in self.current_turn.queue) + "\n\n")
            elif self.current_turn.choosingColor:
                embed.add_field(name="Choose Color", value="{}Red {}Yellow {}Green {}Blue\n\n".format("1⃣","2⃣","3⃣","4⃣"))
            rows = ceil(len(player.hand) / 12)
            emotes = [
                "<:blank:594342155565400114>",
                "\U000025c0",
                "1⃣",
                "2⃣",
                "3⃣",
                "4⃣",
                "5⃣",
                "6⃣",
                "\U000025b6",
            ]
            emojis = []

            if not player.turnOver:
                start = max(0, min(player.page * 6, len(player.hand) - 6))
                end = start + 5
                legalCards = player.getLegalCards()

                index = 0
                for card in player.hand:
                    if index < (start - 1):
                        emojis.append(emotes[0])
                    elif index < start:
                        emojis.append(emotes[1])
                    elif index <= end:
                        emojis.append(emotes[index-start+2])
                    elif index <= (end + 1):
                        emojis.append(emotes[8])
                    else:
                        emojis.append(emotes[0])
                    index += 1
            else:
                for card in player.hand:
                    emojis.append(emotes[0])

            embed.add_field(name=player.user.username + "'s Hand",
                            value=''.join(emojis[0:12]) + "\n" + self.print_hand_menu(player, 0))
            for x in range(ceil(len(player.hand) / 12)):
                if x == 0:
                    continue
                embed.add_field(name=''.join(emojis[(12 * x):(12 * (x + 1))]),
                                value=self.print_hand_menu(player, x))

            if player.hint != "":
                embed.add_field(name="Hint", value=player.hint)
            player.message.edit('', embed=embed)
    def print_player_list(self):
        msg = "```diff\n"
        for player in self.players:
            msg += "{}{}{}: {} card{}\n".format(
                "+ " if self.current_turn.user.id == player.user.id else "",
                player.user.username,
                "'s turn" if self.current_turn.user.id == player.user.id else "",
                len(player.hand),
                "s" if len(player.hand) > 1 else "")
        return msg + "```"

    def print_hand_menu(self, player, line):
        return ''.join(str(x) for x in player.hand[(12 * line):(12 * (line + 1))])

    def setup_players(self, players):
        random.shuffle(players)
        for player in players:
            self.settings.addPlayer(player)
        self.current_turn = self.settings.players[0]
        self.current_turn.startTurn()
        return self.settings.players

    def create_channels(self, players):
        guild_obj = Guild.using_id(self.guild.id)
        channels = []
        for player in players:
            channel_name = "uno-{}-{}".format(self.game_id, player.user)
            channel_name = channel_name.replace('#', '-')
            channel = self.guild.create_channel(parent_id=guild_obj.games_category, name=channel_name,
                                            channel_type=ChannelType.GUILD_TEXT)
            self.update_permissions(channel, guild_obj, player)
            player.message = channel.send_message("Game starting...")
            channels.append(channel)
        return channels

    def update_permissions(self, channel, guild_obj, current_player):
        for x in self.guild.roles:
            role = self.guild.roles.get(x)
            if str(role) == '@everyone':
                ow = channel.create_overwrite(entity=role)
                ow.deny.add(Permissions.SEND_MESSAGES)
                ow.deny.add(Permissions.READ_MESSAGES)
                ow.deny.add(Permissions.MANAGE_MESSAGES)
                ow.deny.add(Permissions.ADD_REACTIONS)
                ow.save()

        if len(guild_obj.spectator_roles) > 0:
            for spec in guild_obj.spectator_roles:
                role = self.guild.roles.get(spec)
                ow = channel.create_overwrite(entity=role)
                ow.allow.add(Permissions.READ_MESSAGES)
                ow.save()

        for player in self.players:
            member = self.guild.get_member(player.user)
            ow = channel.create_overwrite(entity=member)
            if player.user.id == current_player.user.id:
                ow.allow.add(Permissions.READ_MESSAGES)
            else:
                ow.deny.add(Permissions.READ_MESSAGES)
            ow.save()

    def handle_turn(self, event):

        if event.user_id != self.current_turn.user.id or event.message_id != self.current_turn.message.id:
            return False
        if self.game_over:
            return True

        player = self.current_turn

        if event.emoji.id == YES_EMOJI_ID and len(player.queue) > 0:
            self.message_log = "{} placed {} in the pile. ".format(player.user.username, ', '.join(x.name for x in player.queue))
            for card in player.queue:
                if card.value == "DrawTwo":
                    self.pile.drawTwoStacks += 1
                elif card.value == "DrawFour":
                    self.pile.drawFourStacks += 1
                elif card.value == "Skip":
                    self.pile.skipStacks += 1
                elif card.value == "Reverse":
                    self.reverse = not self.reverse
                self.pile.add_card(player.queue.pop(0))
                player.hand.removeCard(player.hand.getIndex(card))

            if self.pile.top_card.wild:
                player.choosingColor = True
                self.update_messages()
                return False

            player.endTurn()
            return False

        if event.emoji.id == NO_EMOJI_ID and len(player.queue) > 0:
            player.queue.pop()
            return False

        if event.emoji.id == NO_EMOJI_ID:
            self.message_log = "{} drew a card. ".format(player.user.username)
            player.draw()
            player.endTurn()
            return False

        place = None
        self.selected = None
        if event.emoji.id != YES_EMOJI_ID:

            switcher = {
                "\U000025c0": "left",
                "1⃣": 0,
                "2⃣": 1,
                "3⃣": 2,
                "4⃣": 3,
                "5⃣": 4,
                "6⃣": 5,
                "\U000025b6": "right"
            }
            place = switcher.get(event.emoji.name, None)

            self.selected = place
        if self.selected == None:

            return False



        if self.selected == "left":
            player.page = max(0, player.page - 1)
            self.update_messages(True)
            return False
        if self.selected == "right":
            player.page = min(ceil(len(player.hand) / 12), player.page + 1)
            self.update_messages(True)
            return False
        card = None
        if isinstance(self.selected, int) and player.choosingColor:

            if self.selected < 4:
                self.pile.top_card.changeColor(list(self.deck.colors)[self.selected])
                player.choosingColor = False
                self.message_log = "The color is now " + self.pile.top_card.color + ". "
                player.endTurn()
                return False
        elif isinstance(self.selected, int) and len(player.queue) == 0:

            card = player.checkLegalCard(max(0, min(player.page * 6, len(player.hand) - 6)) + self.selected)
            if card == None:
                return False
            player.addCardToQueue(card)

        isOver = False

        return isOver
class Player():
    def __init__(self, user, controller):
        self.user = user
        self.type = 'Human'
        self.hand = Hand(controller.deck)
        self.page = 0
        self.legal_cards = []
        self.turnOver = True
        self.deck = controller.deck
        self.pile = controller.pile
        self.message = None
        self.settings = controller.settings
        self.controller = controller
        self.hint = ""
        self.queue = []
        self.choosingColor = False


    def destroy(self):
        for card in self.hand:
            self.deck.addCard(card)

    def startTurn(self):
        self.turnOver = False
        self.controller.messageLog = ""
        if len(self.getLegalCards()) == 0:
            if self.pile.drawTwoStacks > 0 or self.pile.drawFourStacks > 0:
                self.controller.log_message = "{} drew {} cards. ".format(self.user.username, self.pile.drawTwoStacks + self.pile.drawFourStacks, self.getNextPlayer().user.username)
                self.draw(self.pile.drawTwoStacks + self.pile.drawFourStacks)
                self.pile.reset()
                self.endTurn()
                return
            elif self.pile.skipStacks > 0:
                if self.pile.skipStacks == 1:
                    self.endTurn(True)
                else:
                    self.endTurn(False)
                self.pile.skipStacks -= 1

                return
            else:
                self.hint = "Press {} to draw.".format(NO_EMOJI)
                return

    def endTurn(self, update_log=True):
        self.turnOver = True
        self.clearHint()
        self.controller.current_turn = self.getNextPlayer()
        if update_log:
            self.controller.log_message += "It is now {}'s turn.".format(self.controller.current_turn.user.username)
        self.controller.current_turn.startTurn()
        self.controller.update_messages()



    def clearHint(self):
        self.hint = ""

    def addCardToQueue(self, card):
        self.queue.append(card)
        self.controller.update_messages(True)


    def getNextPlayer(self):
        index = self.settings.players.index(self)
        if self.controller.reverse:
            if index - 1 < 0:
                return self.settings.players[len(self.settings.players) - 1]
            else:
                return self.settings.players[index - 1]
        else:
            if index + 1 == len(self.settings.players):
                return self.settings.players[0]
            else:
                return self.settings.players[index + 1]

    def checkLegalCard(self, index):
        if index > len(self.hand):
            return None
        if self.hand[index] in self.legalCards:
            return self.hand[index]
        else:
            return None

    def getLegalCards(self):
        self.legalCards = []
        for card in self.hand:
            if self.settings.rules.stack_draws and self.pile.drawTwoStacks > 0:
                if card.value == "DrawTwo":
                    self.legalCards.append(card)
                break
            elif self.settings.rules.stack_draws and self.pile.drawFourStacks > 0:
                if card.value == "DrawFour":
                    self.legalCards.append(card)
                break
            elif self.settings.rules.cancel_skip and self.pile.skipStacks > 0:
                if card.value == "Skip":
                    self.legalCards.append(card)
                break
            elif self.pile.drawTwoStacks > 0 or self.pile.drawFourStacks > 0 or self.pile.skipStacks > 0:
                break
            if card.color == self.pile.top_card.color:
                self.legalCards.append(card)
                break
            if card.value == self.pile.top_card.value:
                self.legalCards.append(card)
                break
            if card.wild:
                self.legalCards.append(card)
                break
        return self.legalCards
    def draw(self, numCards=1):
        for x in range(numCards):
            self.hand.addCard(self.controller.deck.draw())

class Hand():
    def __init__(self, deck, numCards=7):
        self.hand = []
        self.hand += deck.draw(numCards)

    def __iter__(self):
        return iter(self.hand)

    def __len__(self):
        return len(self.hand)

    def __getitem__(self, item):
        try:
            return self.hand[item]
        except:
            return ''

    def __str__(self):
        return ''.join(str(x)for x in self.hand)

    def addCard(self, card):
        self.hand.append(card)

    def getCard(self, index):
        return self.hand[index]

    def getIndex(self, card):
        return self.hand.index(card)

    def removeCard(self, index):
        self.hand.pop(index)

    def show(self, page=0):
        return ', '.join(self.hand)

class Deck():
    colors = ('Red', 'Yellow', 'Green', 'Blue')
    values = ('0','1','2','3','4','5','6','7','8','9','Skip','Reverse','DrawTwo')

    def __init__(self):
        self.deck = []
        # Populate deck
        for color in self.colors:
            for value in self.values:
                self.deck.append(Card(color, value))
                if value != '0':
                    self.deck.append(Card(color, value))
            for x in range(4):
                self.deck.append(Card('Wild', 'DrawFour'))
                self.deck.append(Card('Wild', ''))
            random.shuffle(self.deck)

    def __iter__(self):
        return iter(self.deck)

    def __len__(self):
        return len(self.deck)

    def draw(self, numCards=1):
        if numCards > 1:
            cards = []
            for x in range(numCards):
                cards.append(self.deck.pop())
            return cards
        else:
            return self.deck.pop()

    def addCard(self, card):
        self.deck.append(card)

class Pile():
    def __init__(self, card):
        self.top_card = card
        self.drawTwoStacks = 0
        self.drawFourStacks = 0
        self.skipStacks = 0

    def add_card(self, card):
        self.top_card = card

    def get_card(self):
        return self.top_card

    def reset(self):
        self.drawTwoStacks = 0
        self.drawFourStacks = 0
        self.skipStacks = 0

class Card():
    def __init__(self, color, value):
        self.wild = color == 'Wild'
        self.color = color
        self.value = value
        self.name = self.color + self.value
        self.emoji_id = bot_config.uno_emojis[self.name].split(':')[1]
        self.emoji = "<:" + bot_config.uno_emojis[self.name] + ">"

    def __str__(self):
        return self.emoji

    def getColor(self):
        return self.color

    def getValue(self):
        return self.value

    def changeColor(self, color):
        self.color = color
        self.name = self.color + self.value

        self.emoji_id = bot_config.uno_emojis[self.name].split(':')[1]
        self.emoji = "<:" + bot_config.uno_emojis[self.name] + ">"

class GameSettings():
    def __init__(self, controller):
        self.players = []
        self.numPlayers = 0
        self.controller = controller
        self.rules = self.set_rules()

    def atPlayerLimit(self):
        return (self.numPlayers == 8)

    def canStart(self):
        return (self.numPlayers > 1)

    def addPlayer(self, user):
        self.players.append(Player(user, self.controller))
        self.numPlayers += 1

    def removePlayer(self, index):
        self.players[index].destroy()
        del self.players[index]
        self.numPlayers -= 1

    def getPlayerSize(self):
        return self.numPlayers

    def set_rules(self):
        enabled_rules = Users.with_id(self.controller.who_started.id).get_enabled()
        if Users.UnoRules.jump_in in enabled_rules:
            Rules.jump_in = True
        if Users.UnoRules.stack_draws in enabled_rules:
            Rules.stack_draws = True
        if Users.UnoRules.seven_swap in enabled_rules:
            Rules.seven_swap = True
        if Users.UnoRules.super_swap in enabled_rules:
            Rules.super_swap = True
        if Users.UnoRules.cancel_skip in enabled_rules:
            Rules.cancel_skip = True
        if Users.UnoRules.special_multiplay in enabled_rules:
            Rules.special_multiplay = True
        if Users.UnoRules.trains in enabled_rules:
            Rules.trains = True
        if Users.UnoRules.endless_draw in enabled_rules:
            Rules.endless_draw = True
        
        return Rules

class Match():
    def __init__(self, settings):
        self.pile = Pile()
        self.players = settings.players
        self.turn = 0
        self.reversed = False
        self.event = ''

class Rules(object):
    jump_in = False 
    stack_draws = False
    seven_swap = False
    super_swap = False
    cancel_skip = False
    special_multiplay = False
    trains = False
    endless_draw = False


