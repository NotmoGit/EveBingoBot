# EveBingoBot
An Eve Online Discord bot for generating and tracking an Eve themed bingo game

## Installation

### config.env

Needs you bot token and the discord IDs for admins

### status.json

Needs to not be an empty file when the bot is loaded

### tasks.json

Needs to not be empty - not tested with under 25 tasks but why would you do that.

### dependencies

discord, discord.ext, json, random, os, dotenv, PIL, io, ast, textwrap, datetime

## Usage

Hit !commands, !rules and !admincommands

## TODO
- It's not really catching errors correctly
- ~~@everyone (or @admin) when the first line, row, diagonal is completed~~  
- create a log of all the completions so that an admin can DM the bot and get the list to go through  
- ~~Come up with a better name~~  
- Create a toggle system in the tasks list for turning things on and off  
- Consider a grouping or weighting system for the task list  
- Create a command to "query" a square and get the kill mail back  
- ~~Create a history system to save the status.json when a new game is created~~
