# GamesKeeper
The GamesKeeper is a Discord bot that was written for Discord Hackweek 2019. Consisting of some of your favorite games you know and love!

## Add the bot to your server.
To add the bot to your server, you can use one of two links:
* [With Needed Permissions](https://discordapp.com/oauth2/authorize?client_id=594004184018190337&scope=bot&permissions=322640)
* [Without Any Permissions](https://discordapp.com/oauth2/authorize?client_id=594004184018190337&scope=bot&permissions=0)

### Permissions Breakdown
- Manage channels is needed to create game channels
- embed/attach files for help command/any misc files that need to be sent.
- Add reactions which some games depend on
- Manage messages to remove command messages
- External Emojis is needed because almost all emojis used are custom.

## Team
* Justin#1337
> Lead Developer (Connect 4/Base bot)
* Nadie#0063
> Developer (Hangman/Database)
* Rina#5040
> Developer (2048)
* Zeboto#0001
> Developer (Uno)
* joaoh1#3657
> Artist (Maker of the Ultimate Assets Pack)

## Testers

* Andeh#0001
* AppleLilly#2015
* astrohaley#0804
* Dropheart#6441
* Duck#6969
* Eagle#3636

## Games

* Uno
* Connect 4
* Hangman
* Tic-Tac-Toe

## Basic Commands

Default prefix is `+`

### Current List of Commands

* Core

General Help Command
> +help [Command Name]

Shows Generic Help Message
> +help

Help with Settings
> +help settings

* Settings

To check server Settings.
> +settings 

To update server prefix.
> +update prefix [Prefix]

Up update Games Category
> +update gc [Channel ID]

To update the Referee role
> +update ref [Role Name or Role ID]

To update Spectator roles
> +update addspec/rvmspec [Role Name or Role ID]

To Enable or Disable a game
> +games enable/disable [Game Name]

## Setup and Install (For Self Hosting)

### Requirements
*Note: These steps are for linux systems. The bot has not been tested in a windows environment.*

* Python 3
* Pip 3
* Postgresql 11

*Note:* 
*After installing postgres, please run `sudo -su postgres psql` and enter `\password` to change the password*
*If you wish to use a different database name, please change the **database** variable in the config and correct the name in the commands below*

### Steps

1. Git clone or download src and extract to folder.
2. Edit the example-config.yaml with a bot token, and save as config.yaml
3. Run the commands below

```sh
$ sudo apt-get install libpq-dev
$ pip3 install -r requirements.txt
$ sudo -u postgres psql -v ON_ERROR_STOP=1 -d gameskeeper -c "CREATE EXTENSION hstore;"
$ sudo -u postgres psql -v ON_ERROR_STOP=1 -d gameskeeper -c "CREATE EXTENSION pg_trgm;"
```

4. To start the bot use the command `python3 -m disco.cli --config config.yaml`