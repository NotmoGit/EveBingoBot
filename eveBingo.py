import discord
from discord.ext import commands
import json
import random
import os
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import io
import ast
import textwrap

# Load bot token from config.env
load_dotenv(dotenv_path="config.env")
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
ADMIN_IDS = ast.literal_eval(os.getenv("ADMIN_ID", "[]"))
if TOKEN is None:
    raise ValueError("DISCORD_BOT_TOKEN not found in environment variables!")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

TASKS_FILE = "tasks.json"
STATUS_FILE = "status.json"
TOKEN_START = 3  # Tokens for regenerating bingo card

# -----------------------------
# Helper functions
# -----------------------------

def load_tasks():
    with open(TASKS_FILE, "r") as f:
        return json.load(f)

def load_status():
    if not os.path.exists(STATUS_FILE):
        return {"players": {}}
    with open(STATUS_FILE, "r") as f:
        return json.load(f)

def save_status(status):
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)

def generate_card():
    tasks = load_tasks()
    sampled = random.sample(tasks, 25)
    squares = [f"{row}{col}" for row in "ABCDE" for col in "12345"]
    return {sq: {"task": task, "completed": False, "proof_link": None} 
            for sq, task in zip(squares, sampled)}

def count_completed_squares(card):
    return sum(1 for sq in card.values() if sq["completed"])

def get_completed_lines(card):
    """Return a list of completed lines (rows, columns, diagonals) for highlighting."""
    lines = []
    rows = "ABCDE"
    cols = "12345"
    # Rows
    for r in rows:
        if all(card[f"{r}{c}"]["completed"] for c in cols):
            lines.append([f"{r}{c}" for c in cols])
    # Columns
    for c in cols:
        if all(card[f"{r}{c}"]["completed"] for r in rows):
            lines.append([f"{r}{c}" for r in rows])
    # Diagonals
    if all(card[f"{rows[i]}{cols[i]}"]["completed"] for i in range(5)):
        lines.append([f"{rows[i]}{cols[i]}" for i in range(5)])
    if all(card[f"{rows[i]}{cols[4-i]}"]["completed"] for i in range(5)):
        lines.append([f"{rows[i]}{cols[4-i]}" for i in range(5)])
    return lines

def count_completed_lines(card):
    return len(get_completed_lines(card))

def generate_card_image(card):
    """Generates a bingo card image with row/column labels and better line spacing."""
    size = 550  # slightly larger to accommodate labels
    square_size = 100  # size of each square
    font = ImageFont.load_default()  # replace with TTF if desired
    label_font = ImageFont.load_default()

    img = Image.new("RGB", (size, size), color="white")
    draw = ImageDraw.Draw(img)

    rows = "ABCDE"
    cols = "12345"
    label_offset = 20  # space for labels

    # Draw row labels (left)
    for i, r in enumerate(rows):
        bbox = draw.textbbox((0, 0), r, font=label_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        y = label_offset + i * square_size + (square_size - text_height) / 2
        draw.text((5, y), r, fill="black", font=label_font)

    # Draw column labels (top)
    for j, c in enumerate(cols):
        bbox = draw.textbbox((0, 0), c, font=label_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = label_offset + j * square_size + (square_size - text_width) / 2
        draw.text((x, 5), c, fill="black", font=label_font)

    # Draw squares
    for i, r in enumerate(rows):
        for j, c in enumerate(cols):
            index = f"{r}{c}"
            square = card[index]

            # Determine fill color
            if index == "C3":
                fill = "orange" if square.get("completed") else "gold"
            elif square.get("completed") and square.get("verified"):
                fill = "limegreen"
            elif square.get("completed"):
                fill = "lightgreen"
            else:
                fill = "lightgray"

            top_left = (label_offset + j * square_size, label_offset + i * square_size)
            bottom_right = (label_offset + (j + 1) * square_size, label_offset + (i + 1) * square_size)
            draw.rectangle([top_left, bottom_right], fill=fill, outline="black")

            # Wrap text
            max_chars_per_line = 15
            wrapped_text = textwrap.fill(square["task"], width=max_chars_per_line)
            lines = wrapped_text.split("\n")

            # Compute total height
            line_heights = []
            line_widths = []
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                lw = bbox[2] - bbox[0]
                lh = bbox[3] - bbox[1]
                line_widths.append(lw)
                line_heights.append(lh)
            line_spacing = 4
            total_height = sum(line_heights) + line_spacing * (len(lines) - 1)

            # Draw text centered with spacing
            y_offset = top_left[1] + (square_size - total_height) / 2
            for line, lh, lw in zip(lines, line_heights, line_widths):
                x = top_left[0] + (square_size - lw) / 2
                draw.text((x, y_offset), line, fill="black", font=font)
                y_offset += lh + line_spacing

    # Save to bytes buffer
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# -----------------------------
# Player Commands
# -----------------------------

@bot.command()
async def enter(ctx):
    """Add a player to the list."""
    status = load_status()
    player_id = str(ctx.author.id)
    if player_id in status["players"]:
        await ctx.send(f"{ctx.author.display_name}, you are already entered!")
        return
    status["players"][player_id] = {
        "username": ctx.author.display_name,
        "tokens": TOKEN_START,
        "card": None
    }
    save_status(status)
    await ctx.send(f"{ctx.author.display_name} has been entered into the game!")

@bot.command()
async def rules(ctx):
    """Display the rules of the EVE Bingo game."""
    rules_list = [
        "1. 100m buy in",
        "2. First to get a line gets 10% of prize pool",
        "3. First to get a row gets 10% of prize pool",
        "4. First to get a diagonal gets 15% of prize pool",
        "5. First to get BINGO gets the rest",
        "6. No gaming the system",
        "7. No duplicate kills",
        "8. Final rules decisions will be made by Notmo",
        "9. Generation templates can be purchased for 20m",
        '10. Submissions for "A Very Special Kill" should be made directly by DM to Notmo (with story if it\'s not obvious) - you may resubmit at any time before the end of the competition'
    ]

    embed = discord.Embed(title="EVE Bingo Rules", color=0x0000ff)
    embed.description = "\n".join(rules_list)
    await ctx.send(embed=embed)

@bot.command()
async def generate(ctx):
    """Generate a 25-square bingo card for the player, center is special."""
    status = load_status()
    player_id = str(ctx.author.id)

    if player_id not in status["players"]:
        await ctx.send("You need to !enter first.")
        return

    player = status["players"][player_id]

    if player.get("tokens", 1) <= 0:
        await ctx.send("You have no tokens left to generate a new card.")
        return

    player["tokens"] = player.get("tokens", 1) - 1

    with open("tasks.json", "r") as f:
        tasks = json.load(f)

    chosen_tasks = random.sample(tasks, 24)

    card = {}
    rows = "ABCDE"
    cols = "12345"
    idx = 0
    for i, r in enumerate(rows):
        for j, c in enumerate(cols):
            square_index = f"{r}{c}"
            if square_index == "C3":
                card[square_index] = {"task": "A very special kill", "completed": False, "proof_link": None}
            else:
                card[square_index] = {"task": chosen_tasks[idx], "completed": False, "proof_link": None}
                idx += 1

    player["card"] = card
    save_status(status)

    img_buf = generate_card_image(card)
    await ctx.send(f"{ctx.author.display_name}, your new bingo card has been generated!", 
                   file=discord.File(fp=img_buf, filename="bingo_card.png"))

@bot.command()
async def tokens(ctx):
    status = load_status()
    player_id = str(ctx.author.id)
    if player_id not in status["players"]:
        await ctx.send("You need to !enter first.")
        return
    tokens = status["players"][player_id]["tokens"]
    await ctx.send(f"{ctx.author.display_name}, you have {tokens} token(s) left.")

@bot.command()
async def complete(ctx, index: str, link: str = None):
    if link is None:
        await ctx.send("You must provide a proof link! Usage: `!complete [index] [link]`")
        return

    status = load_status()
    player_id = str(ctx.author.id)

    if player_id not in status["players"]:
        await ctx.send("You need to !enter first.")
        return

    player = status["players"][player_id]

    if not player.get("card"):
        await ctx.send("You need to !generate a card first.")
        return

    index = index.upper()
    if index not in player["card"]:
        await ctx.send("Invalid square index! Use A1-E5.")
        return
    if player["card"][index]["completed"]:
        await ctx.send("This square is already completed!")
        return

    if not link.startswith("https://zkillboard.com/"):
        await ctx.send("Invalid link domain! Must be from zkillboard")
        return

    for sq_index, sq_data in player["card"].items():
        if sq_data.get("proof_link") == link:
            await ctx.send("You have already used this link for another square!")
            return

    player["card"][index]["completed"] = True
    player["card"][index]["proof_link"] = link
    save_status(status)

    # Notify about completed lines
    total_lines = count_completed_lines(player["card"])
    msg = f"{ctx.author.display_name}, square {index} marked complete!"
    if total_lines > 0:
        msg += f" 🎉 You now have {total_lines} full line(s) completed!"

    await ctx.send(msg)

@bot.command()
async def progress(ctx, member: discord.Member = None):
    status = load_status()
    if member is None:
        member = ctx.author
    player_id = str(member.id)
    if player_id not in status["players"]:
        await ctx.send("Player not found.")
        return
    player = status["players"][player_id]
    if not player["card"]:
        await ctx.send("Player has no card yet.")
        return
    total_squares = count_completed_squares(player["card"])
    total_lines = count_completed_lines(player["card"])
    await ctx.send(f"{member.display_name}'s Progress: {total_squares} squares completed, {total_lines} full lines.")

@bot.command()
async def mycard(ctx):
    status = load_status()
    player_id = str(ctx.author.id)

    if player_id not in status["players"]:
        await ctx.send("You need to !enter first.")
        return

    player = status["players"][player_id]

    if not player.get("card"):
        await ctx.send("You need to !generate a card first.")
        return

    img_buf = generate_card_image(player["card"])
    await ctx.send(f"{ctx.author.display_name}, here is your current bingo card:", 
                   file=discord.File(fp=img_buf, filename="bingo_card.png"))

@bot.command()
async def commands(ctx):
    command_list = {
        "!rules": "Read the rules",
        "!enter": "Enter the game.",
        "!generate": "Generate a bingo card. Regenerating uses a token.",
        "!tokens": "Show how many card regeneration tokens you have left.",
        "!complete [index] [link]": "Mark a square complete with a proof link (zkillboard link only).",
        "!progress [player]": "Show progress of yourself or another player.",
        "!mycard": "Show your current bingo card with completed squares highlighted."
    }

    embed = discord.Embed(title="EVE Bingo Commands", color=0x00ff00)
    for cmd, desc in command_list.items():
        embed.add_field(name=cmd, value=desc, inline=False)

    await ctx.send(embed=embed)

# -----------------------------
# Admin Commands
# -----------------------------
def is_admin(ctx):
    return ctx.author.id in ADMIN_IDS

@bot.command()
async def newgame(ctx):
    if not is_admin(ctx):
        await ctx.send("You are not authorized!")
        return
    save_status({"players": {}})
    await ctx.send("New game started! All players and cards cleared.")

@bot.command()
async def verify(ctx, member: discord.Member, index: str):
    if not is_admin(ctx):
        await ctx.send("You are not authorized!")
        return

    status = load_status()
    player_id = str(member.id)
    if player_id not in status["players"]:
        await ctx.send("Player not found.")
        return

    player = status["players"][player_id]
    if not player["card"]:
        await ctx.send("Player has no card.")
        return

    index = index.upper()
    if index not in player["card"]:
        await ctx.send("Invalid square index.")
        return

    player["card"][index]["verified"] = True
    save_status(status)
    await ctx.send(f"Verified {member.display_name}'s square {index}.")

@verify.error
async def verify_error(ctx, error):
    if isinstance(error, commands.MemberNotFound):
        await ctx.send(
            "Member not found! Make sure you mention the player first, then the square index.\n"
            "Correct usage: `!verify @player C3`"
        )
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing arguments! Usage: `!verify @player [index]`")
    else:
        raise error

@bot.command()
async def status(ctx):
    status_data = load_status()
    leaderboard = []
    for p_id, player in status_data["players"].items():
        completed = count_completed_squares(player["card"]) if player.get("card") else 0
        leaderboard.append((player["username"], completed))
    leaderboard.sort(key=lambda x: x[1], reverse=True)
    msg = "🏆 Leaderboard 🏆\n"
    for i, (name, completed) in enumerate(leaderboard[:10], start=1):
        msg += f"{i}. {name}: {completed} squares\n"
    await ctx.send(msg)

@bot.command()
async def reject(ctx, member: discord.Member, index: str):
    if not is_admin(ctx):
        await ctx.send("You do not have permission to use this command.")
        return

    status = load_status()
    player_id = str(member.id)

    if player_id not in status["players"]:
        await ctx.send(f"{member.display_name} is not in the player list.")
        return

    player = status["players"][player_id]
    index = index.upper()

    if index not in player.get("card", {}):
        await ctx.send("Invalid square index! Use A1-E5.")
        return

    player["card"][index]["completed"] = False
    player["card"][index]["proof_link"] = None
    save_status(status)

    await ctx.send(f"{member.display_name}'s square {index} has been reset.")

@bot.command()
async def addtokens(ctx, member: discord.Member, amount: int):
    if not is_admin(ctx):
        await ctx.send("You do not have permission to use this command.")
        return

    if amount <= 0:
        await ctx.send("Please provide a positive number of tokens.")
        return

    status = load_status()
    player_id = str(member.id)

    if player_id not in status["players"]:
        await ctx.send(f"{member.display_name} is not in the player list.")
        return

    player = status["players"][player_id]
    player["tokens"] = player.get("tokens", 0) + amount
    save_status(status)

    await ctx.send(f"{member.display_name} has been given {amount} extra token(s). They now have {player['tokens']} tokens.")

@bot.command()
async def admincommands(ctx):
    if not is_admin(ctx):
        await ctx.send("You do not have permission to view admin commands.")
        return

    admin_command_list = {
        "!newgame": "Start a new game. Clears all players and cards.",
        "!verify [player] [index]": "Verify a player's square kill link.",
        "!status": "Show the leaderboard (top 10 by completed squares).",
        "!reject [player] [index]": "Reset a specific square of a player.",
        "!addtokens [player] [amount]": "Give extra card regeneration tokens to a player."
    }

    embed = discord.Embed(title="EVE Bingo Admin Commands", color=0xff0000)
    for cmd, desc in admin_command_list.items():
        embed.add_field(name=cmd, value=desc, inline=False)

    await ctx.send(embed=embed)

# -----------------------------
# Run the bot
# -----------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
