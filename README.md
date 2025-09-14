# EveBingoBot
An Eve Online Discord bot for generating and tracking an Eve themed bingo game

##General Commands:
!rules
Read the rules
!enter
Enter the game.
!generate
Generate a bingo card. Regenerating uses a token.
!tokens
Show how many card regeneration tokens you have left.
!complete [index] [link]
Mark a square complete with a proof link (zkillboard link only).
!progress [player]
Show progress of yourself or another player.
!mycard
Show your current bingo card with completed squares highlighted.

##Admin Commands:
!newgame
Start a new game. Clears all players and cards.
!verify [player] [index]
Verify a player's square kill link.
!status
Show the leaderboard (top 10 by completed squares).
!reject [player] [index]
Reset a specific square of a player.
!addtokens [player] [amount]
Give extra card regeneration tokens to a player.

##Installation

#config.env

Needs you bot token and the discord IDs for admins

#status.json

Needs to not be an empty file when the bot is loaded

#tasks.json

Needs to not be empty - not tested with under 25 tasks but why would you do that.

#dependencies

discord, discord.ext, json, random, os, dotenv, PIL, io, ast, textwrap

##TODO
- It's not really catching errors correctly
- @everyone (or @admin) when the first line, row, diagonal is completed
- create a log of all the completions so that an admin can DM the bot and get the list to go through
- Come up with a better name
- Create a toggle system in the tasks list for turning things on and off
- Consider a grouping or weighting system for the task list
- Create a command to "query" a square and get the kill mail back
- Create a history system to save the status.json when a new game is created
