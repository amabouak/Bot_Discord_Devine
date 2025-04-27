import discord
from discord.ext import commands
import random

# Préfixe pour les commandes
bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

# Liste de blagues
blagues = [
    "Pourquoi les plongeurs plongent-ils toujours en arrière et jamais en avant ? Parce que sinon ils tombent dans le bateau ! 🚤",
    "Que dit une imprimante dans l'eau ? J'ai papier ! 🖨️💦",
    "Pourquoi les poissons détestent l’ordinateur ? À cause d’Internet. 🐟💻",
    "Quel est le comble pour un électricien ? De ne pas être au courant. ⚡",
    "Pourquoi les squelettes ne se battent-ils jamais entre eux ? Ils n'ont pas le cran. ☠️"
]

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user} !")

@bot.command()
async def blague(ctx):
    blague = random.choice(blagues)
    await ctx.send(blague)

# Remplace "TON_TOKEN_ICI" par ton token
bot.run("TON_TOKEN_ICI")
