# -*- coding: utf-8 -*-
from GamesKeeper.models.guild import Guild

from disco.types.permissions import Permissions
from disco.types.channel import ChannelType
from disco.types.message import MessageEmbed

import random
import requests

class hangman():
    def __init__(self, event):
        self.start_event = event
        self.guild = event.guild
        #get word to be used
        self.word = self.get_random_word()
        self.word_dissisembled = list(self.word)
        self.word_current = ["_"] * len(self.word_dissisembled)
        self.failed_attempts = 0
        self.attempts_made = 0
        self.usedchars = list()
        self.game_channel = self.create_channel(self.start_event.author)
        self.main_msg = self.create_message()
        self.update_status(None)

    def get_random_word(self):
        word = None
        #uses large text file full of words and picks a random one
        r = requests.get("https://www.randomlists.com/data/words.json")
        word = random.choice(r.json()["data"])
        return "{}".format(word).lower()

    def create_message(self):
        msgcontent = "**Word**: " + " ".join(self.word_to_emote(self.word_current))
        embed = MessageEmbed()
        embed.set_image(url=self.get_hangman_image(self.failed_attempts))
        return self.game_channel.send_message(msgcontent, embed=embed)

    def update_msg(self):
        msgcontent = "**Word**: " + " ".join(self.word_to_emote(self.word_current))
        embed = MessageEmbed()
        embed.set_image(url=self.get_hangman_image(self.failed_attempts))
        self.main_msg.edit(msgcontent, embed=embed)

    def create_channel(self, player):
        guild_obj = Guild.using_id(self.guild.id)

        channel_name = "{}-Hangman".format(player)
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
                ow.deny.add(Permissions.ADD_REACTIONS)
                ow.save()

        if len(guild_obj.spectator_roles) > 0:
            for spec in guild_obj.spectator_roles:
                role = self.guild.roles.get(spec)
                ow = channel.create_overwrite(entity=role)
                ow.allow.add(Permissions.READ_MESSAGES)
                ow.save()

        member = self.guild.get_member(self.start_event.author)
        ow = channel.create_overwrite(entity=member)
        ow.allow.add(Permissions.READ_MESSAGES)
        ow.allow.add(Permissions.SEND_MESSAGES)
        ow.save()

    def update_status(self, Type):
        if Type is None:
            self.game_channel.set_topic("Welcome...")
        if Type is "wrong":
            self.game_channel.set_topic("Invalid Choice, you have {} trys remaining".format(7-int(self.failed_attempts)))
        if Type is "num":
            self.game_channel.set_topic("Numbers are not alowed...")
        if Type is "used":
            self.game_channel.set_topic("That letter has already been used...")
        if Type is "dead":
            self.game_channel.set_topic("R.I.P")
        if Type is "won":
            self.game_channel.set_topic("Congradulations")
        if Type is "correct":
            self.game_channel.set_topic("Correct guess!")

    def get_hangman_image(self, failed_attempts):
        baseurl = "https://assists.aperturebot.science/gameskeeper/hangman"
        if failed_attempts > 7:
            failed_attempts = 7
        return "{}/{}.png".format(baseurl, failed_attempts)

    def word_to_emote(self, currentarray):
        commpletedarray = list()
        for letter in currentarray:
            if letter is "_":
                commpletedarray.append(":HangmanBlank:")
            elif letter is " ":
                commpletedarray.append("-")
            else:
                commpletedarray.append(":Hangman{}:".format(letter.upper()))
        return commpletedarray

    def on_guess(self, guess_event, letter):
        guess = letter[0].lower()

        #check if its a letter
        if guess.isalpha() is False:
            self.update_status("num")
            self.end_guess()
            return

        #check if it already was used
        if guess in self.usedchars:
            self.update_status("used")
            self.end_guess()
            return

        #add char to list.
        self.usedchars.append(guess)

        #count attempt
        self.attempts_made = self.attempts_made + 1

        #check if its in array, if so move it over to the current array then yeet returnm if not found addd a attempted fail
        if guess not in self.word_dissisembled:
            self.failed_attempts = self.failed_attempts +1
            self.update_status("wrong")
            self.end_guess()
        else:
            for i in range(len(self.word_dissisembled)):
                if self.word_dissisembled[i] == guess:
                    self.word_current[i] = guess
        self.end_guess()

    def end_guess(self):
        self.update_msg()
        #check if hangman is dead
        if self.failed_attempts >= 7:
            self.update_status("dead")
            self.game_channel.send_message("You have lost..")
            self.do_exit()
            return

        #check if game has won
        if self.word_dissisembled == self.word_current:
            self.update_status("won")
            self.game_channel.send_message("you have won")
            self.do_exit()
            return

    def do_exit(self):
        #TODO: do something lol

        None