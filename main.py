import discord
from discord.ext import commands, tasks
import sqlite3
import time
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.voice_states = True
intents.messages = True
intents.message_content = True

my_secret = os.environ['DC_TOKEN']

client = commands.Bot(command_prefix='!', intents=intents)

# Connect to SQLite database
conn = sqlite3.connect('voice_chat.db')
c = conn.cursor()

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    if not reset_monthly_voice_time.is_running():
        reset_monthly_voice_time.start()

@client.event
async def on_voice_state_update(member, before, after):
    if before.channel != after.channel or before.self_mute != after.self_mute or before.self_deaf != after.self_deaf:
        if before.channel and (not before.self_mute and not before.self_deaf):
            end_time = int(time.time())
            start_time = client.start_time.get(member.id)
            if start_time:
                total_time = end_time - start_time
                update_time(member.id, member.name, total_time)
        if after.channel and (not after.self_mute and not after.self_deaf):
            client.start_time[member.id] = int(time.time())

def update_time(user_id, username, time_in_voice):
    now = datetime.now()
    month_year = now.strftime("%Y-%m")
    c.execute('SELECT * FROM voice_chat_time WHERE user_id = ? AND month_year = ?', (user_id, month_year))
    data = c.fetchone()

    if data is None:
        c.execute('''INSERT INTO voice_chat_time (user_id, username, time_in_voice, month_year)
                     VALUES (?, ?, ?, ?)''', (user_id, username, time_in_voice, month_year))
    else:
        c.execute('''UPDATE voice_chat_time
                     SET time_in_voice = time_in_voice + ?
                     WHERE user_id = ? AND month_year = ?''', (time_in_voice, user_id, month_year))

    conn.commit()

@client.command()
async def voicetime(ctx, username: str = None):
    if username:
        c.execute('SELECT user_id FROM voice_chat_time WHERE username = ? ORDER BY id DESC LIMIT 1', (username,))
        user_data = c.fetchone()
        if user_data:
            user_id = user_data[0]
        else:
            await ctx.send(f"User {username} not found.")
            return
    else:
        user_id = ctx.author.id
        username = ctx.author.name

    month_year = datetime.now().strftime('%Y-%m')
    c.execute('SELECT time_in_voice FROM voice_chat_time WHERE user_id = ? AND month_year = ?', (user_id, month_year))
    data = c.fetchone()

    if data is None:
        await ctx.send(f"{username}, you haven't spent any time in voice chat this month.")
    else:
        total_time = data[0]
        hours, remainder = divmod(total_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        await ctx.send(f"{username}, you have spent {hours} hours, {minutes} minutes, and {seconds} seconds in voice chat this month.")

@client.command()
async def leaderboard(ctx):
    month_year = datetime.now().strftime('%Y-%m')
    c.execute('SELECT username, time_in_voice FROM voice_chat_time WHERE month_year = ? ORDER BY time_in_voice DESC LIMIT 10', (month_year,))
    leaderboard_data = c.fetchall()
    if leaderboard_data:
        leaderboard = "\n".join([f"{i+1}. {row[0]}: {row[1] // 3600}h {row[1] % 3600 // 60}m {row[1] % 60}s" for i, row in enumerate(leaderboard_data)])
        await ctx.send(f"Leaderboard:\n{leaderboard}")
    else:
        await ctx.send("No data available for the leaderboard.")

@tasks.loop(hours=24)
async def reset_monthly_voice_time():
    if datetime.now().day == 1:
        last_month = (datetime.now().replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
        c.execute('INSERT INTO voice_chat_archive (user_id, username, time_in_voice, month_year) SELECT user_id, username, time_in_voice, ? FROM voice_chat_time', (last_month,))
        c.execute('DELETE FROM voice_chat_time')
        conn.commit()

@client.command()
async def pasttime(ctx, month: str, year: int, username: str = None):
    month_mapping = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }

    if month.capitalize() not in month_mapping:
        await ctx.send(f"Invalid month: {month}. Please provide a valid month name.")
        return

    month_number = month_mapping[month.capitalize()]
    month_year = f"{year}-{month_number:02d}"
    
    if username:
        c.execute('SELECT user_id FROM voice_chat_archive WHERE username = ? AND month_year = ? ORDER BY id DESC LIMIT 1', (username, month_year))
        user_data = c.fetchone()
        if user_data:
            user_id = user_data[0]
        else:
            await ctx.send(f"User {username} not found for {month}/{year}.")
            return
    else:
        user_id = ctx.author.id
        username = ctx.author.name

    c.execute('SELECT time_in_voice FROM voice_chat_archive WHERE user_id = ? AND month_year = ?', (user_id, month_year))
    data = c.fetchone()

    if data is None:
        await ctx.send(f"{username}, you haven't spent any time in voice chat for {month}/{year}.")
    else:
        total_time = data[0]
        hours, remainder = divmod(total_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        await ctx.send(f"{username}, you have spent {hours} hours, {minutes} minutes, and {seconds} seconds in voice chat for {month}/{year}.")

# Initialize start_time dictionary
client.start_time = {}

client.run(my_secret)
