import discord
from discord.ext import commands
import random
import os
import asyncio
import json
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TOKEN')

# Configuration des intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  
bot = commands.Bot(command_prefix="!", intents=intents)

# Stocker les parties 
parties = {}

# Configuration des modes
MODES = {
    "facile": {"range": (1, 50), "time": 45},
    "normal": {"range": (1, 100), "time": 30},
    "difficile": {"range": (1, 200), "time": 20},
    "impossible": {"range": (1, 500), "time": 10}
}

# Charger le leaderboard
LEADERBOARD_FILE = "leaderboard.json"

if os.path.exists(LEADERBOARD_FILE):
    with open(LEADERBOARD_FILE, "r") as f:
        game_leaderboard = json.load(f)
else:
    game_leaderboard = {}

if not isinstance(game_leaderboard, dict):
    game_leaderboard = {}

def save_leaderboard():
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(game_leaderboard, f, indent=4)

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user} !")
    await bot.tree.sync()

# Définir la fonction temps_limite avant la commande start
async def temps_limite(interaction, nombre_secret, temps):
    await asyncio.sleep(temps)
    if interaction.guild.id in parties:
        await interaction.channel.send(f"⏰ Temps écoulé ! Le nombre était **{nombre_secret}**. 😢")
        del parties[interaction.guild.id] 

@bot.tree.command(name="start", description="Démarrer une partie avec un mode de difficulté ou personnalisé.")
async def start(interaction: discord.Interaction, mode: str = "normal", min_val: int = None, max_val: int = None, temps: int = None):
    """Démarrer une partie avec un mode de difficulté ou personnalisé."""
    
    # Vérifier si l'interaction provient d'un serveur (guild)
    if interaction.guild is None:
        await interaction.response.send_message("❌ Cette commande ne peut être utilisée que dans un serveur.")
        return
    
    mode = mode.lower()

    if mode == "custom":
        if min_val is None or max_val is None or temps is None:
            await interaction.response.send_message("⚙️ Utilisation correcte pour custom : `/start custom <min> <max> <temps en secondes>`")
            return
        borne_min, borne_max = min_val, max_val
    else:
        if mode not in MODES:
            await interaction.response.send_message(f"⚠️ Mode inconnu ! Choisis parmi : {', '.join(MODES.keys())} ou `custom`.")
            return
        config = MODES[mode]
        borne_min, borne_max = config["range"]
        temps = config["time"]

    if interaction.guild.id in parties:
        await interaction.response.send_message("⚠️ Une partie est déjà en cours ! Utilise `/stop` pour l'arrêter.")
        return

    nombre_secret = random.randint(borne_min, borne_max)
    await interaction.response.send_message(f"🎮 Mode **{mode.capitalize()}** lancé ! Devinez un nombre entre **{borne_min}** et **{borne_max}**.\n⏳ Vous avez **{temps} secondes** !")

    task = asyncio.create_task(temps_limite(interaction, nombre_secret, temps))
    start_time = asyncio.get_event_loop().time()
    parties[interaction.guild.id] = (nombre_secret, interaction.user.id, task, borne_min, borne_max, temps, start_time)

@bot.tree.command(name="stop", description="Arrêter la partie en cours.")
async def stop(interaction: discord.Interaction):
    """Arrêter la partie en cours."""
    if interaction.guild.id in parties:
        _, _, task, _, _, _, _ = parties[interaction.guild.id]
        task.cancel()
        del parties[interaction.guild.id]
        await interaction.response.send_message("🛑 Partie arrêtée.")
    else:
        await interaction.response.send_message("❌ Il n'y a pas de partie en cours.")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    if message.guild.id in parties:
        nombre_secret, joueur_id, task, borne_min, borne_max, temps, start_time = parties[message.guild.id]

        try:
            guess = int(message.content)

            if guess < borne_min or guess > borne_max:
                await message.channel.send(f"{message.author.mention}, ton nombre doit être entre {borne_min} et {borne_max} ! 🔢")
            elif guess < nombre_secret:
                await message.channel.send(f"{message.author.mention} Trop petit ! 📉")
            elif guess > nombre_secret:
                await message.channel.send(f"{message.author.mention} Trop grand ! 📈")
            else:
                end_time = asyncio.get_event_loop().time()
                elapsed_time = int(end_time - start_time)

                await message.channel.send(f"🎉 Bravo {message.author.mention} ! Tu as trouvé le nombre **{nombre_secret}** en **{elapsed_time} secondes** !")

                # Mettre à jour le leaderboard
                user_id = str(message.author.id)
                if user_id not in game_leaderboard:
                    game_leaderboard[user_id] = {"wins": 0, "fastest": elapsed_time}
                game_leaderboard[user_id]["wins"] += 1
                if elapsed_time < game_leaderboard[user_id]["fastest"]:
                    game_leaderboard[user_id]["fastest"] = elapsed_time
                save_leaderboard()

                task.cancel()
                del parties[message.guild.id]

        except ValueError:
            pass

@bot.tree.command(name="leaderboard", description="Afficher le classement.")
async def leaderboard(interaction: discord.Interaction):
    """Afficher le classement."""
    if not game_leaderboard:
        await interaction.response.send_message("📊 Aucun score enregistré encore !")
        return

    # Trier les scores en fonction des victoires et des meilleurs temps
    sorted_leaderboard = sorted(game_leaderboard.items(), key=lambda item: (-item[1]["wins"], item[1]["fastest"]))
    
    # Créer l'embed pour afficher le classement
    embed = discord.Embed(title="🏆 Leaderboard - Devine le Nombre", color=0x00ff00)

    for i, (user_id, data) in enumerate(sorted_leaderboard[:10], 1):
        user = await bot.fetch_user(int(user_id))
        embed.add_field(
            name=f"{i}. {user.name}",
            value=f"Victoires: {data['wins']} | Meilleur temps: {data['fastest']}s",
            inline=False
        )

    await interaction.response.send_message(embed=embed)

# Lancer le bot
bot.run(TOKEN)
