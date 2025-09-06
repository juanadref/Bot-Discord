import discord
from discord import app_commands
from discord.ext import commands
import os
from datetime import datetime

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents)

# ======= Variables =======
tickets_config = {}  
botones_config = {}  

color_map = {
    "amarillo": discord.ButtonStyle.secondary,
    "rojo": discord.ButtonStyle.danger,
    "verde": discord.ButtonStyle.success,
    "azul": discord.ButtonStyle.primary,
    "gris": discord.ButtonStyle.secondary
}

# ======= on_ready =======
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Comandos sincronizados: {len(synced)}")
    except Exception as e:
        print(f"Error al sincronizar comandos: {e}")

# ======= /ticket =======
@bot.tree.command(name="ticket", description="Configurar ticket")
@app_commands.describe(
    titulo="Título del ticket",
    descripcion="Descripción del ticket",
    footer="Pie de página",
    num_botones="Número de botones que tendrá el ticket"
)
async def ticket(interaction: discord.Interaction, titulo: str, descripcion: str, footer: str, num_botones: int):
    tickets_config[interaction.guild.id] = {
        "titulo": titulo,
        "descripcion": descripcion,
        "footer": footer,
        "num_buttons": num_botones
    }
    botones_config[interaction.guild.id] = []  
    await interaction.response.send_message(f"Ticket configurado con {num_botones} botones. Ahora agrega los botones con /boton", ephemeral=True)

# ======= /boton =======
@bot.tree.command(name="boton", description="Agregar un botón al ticket")
@app_commands.describe(
    titulo_boton="Texto que aparecerá en el panel del ticket",
    titulo_panel="Título del embed dentro del canal",
    descripcion="Descripción del embed dentro del canal",
    color="Color del botón (amarillo, rojo, verde, azul, gris)",
    mensaje_dm="Mensaje que recibirá el usuario en DM",
    rol="Rol que verá el canal"
)
async def boton(interaction: discord.Interaction, titulo_boton: str, titulo_panel: str, descripcion: str, color: str, mensaje_dm: str, rol: discord.Role):
    guild_id = interaction.guild.id

    if guild_id not in tickets_config:
        await interaction.response.send_message("Primero debes configurar el ticket con /ticket", ephemeral=True)
        return

    color = color.lower()
    if color not in color_map:
        await interaction.response.send_message("Color inválido. Usa: amarillo, rojo, verde, azul, gris.", ephemeral=True)
        return

    botones_config[guild_id].append({
        "titulo_boton": titulo_boton,
        "titulo_panel": titulo_panel,
        "descripcion": descripcion,
        "color": color,
        "mensaje_dm": mensaje_dm,
        "rol_id": rol.id
    })

    if len(botones_config[guild_id]) >= tickets_config[guild_id]["num_buttons"]:
        embed = discord.Embed(
            title=tickets_config[guild_id]["titulo"],
            description=tickets_config[guild_id]["descripcion"],
            color=discord.Color.blue()
        )
        embed.set_footer(text=tickets_config[guild_id]["footer"])

        view = discord.ui.View()
        for b in botones_config[guild_id]:
            style = color_map[b["color"]]
            view.add_item(discord.ui.Button(label=b["titulo_boton"], style=style, custom_id=f"ticket_{b['titulo_boton']}"))

        await interaction.response.send_message("", embed=embed, view=view)
    else:
        await interaction.response.send_message(f"Botón agregado. {tickets_config[guild_id]['num_buttons'] - len(botones_config[guild_id])} restantes.", ephemeral=True)

# ======= Cerrar ticket button =======
class CloseTicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="❌ | Cerrar ticket", style=discord.ButtonStyle.danger, custom_id="cerrar_ticket"))

# ======= Evento interacción botones =======
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type != discord.InteractionType.component:
        return

    custom_id = interaction.data['custom_id']
    guild_id = interaction.guild.id

    if custom_id == "cerrar_ticket":
        await interaction.channel.delete()
        return

    if custom_id.startswith("ticket_"):
        boton_data = next((b for b in botones_config[guild_id] if f"ticket_{b['titulo_boton']}" == custom_id), None)
        if not boton_data:
            return

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            interaction.guild.get_role(boton_data['rol_id']): discord.PermissionOverwrite(view_channel=True)
        }
        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            overwrites=overwrites
        )

        await channel.send(f"{interaction.user.mention} {interaction.guild.get_role(boton_data['rol_id']).mention}")

        embed = discord.Embed(
            title=boton_data['titulo_panel'],
            description=boton_data['descripcion'],
            color=discord.Color.blue()
        )
        embed.set_footer(text=tickets_config[guild_id]["footer"])

        await channel.send(embed=embed, view=CloseTicketButton())

        try:
            await interaction.user.send(boton_data['mensaje_dm'])
        except:
            await channel.send(f"{interaction.user.mention}, no se pudo enviar el DM.")

        await interaction.response.send_message(f"Ticket creado: {channel.mention}", ephemeral=True)

# ======= /reglasdiscord =======
@bot.command(name="reglasdiscord")
async def reglasdiscord(ctx):
    embed = discord.Embed(
        title="📜 Reglas Discord",
        description="El objetivo de estas reglas es crear un entorno seguro...",
        color=discord.Color.orange()
    )
    embed.set_footer(text="Administracion Jalisco.")
    await ctx.send(embed=embed)

# ======= /reglasrp =======
@bot.command(name="reglasrp")
async def reglasrp(ctx):
    embed = discord.Embed(
        title="🎭 Reglas Roleplay",
        description="Reglas específicas de rol",
        color=discord.Color.purple()
    )
    embed.set_footer(text="Administracion Jalisco.")
    await ctx.send(embed=embed)


# ====== Evento de bienvenida ======
@bot.event
async def on_member_join(member: discord.Member):
    canal_id = 1177497499431346247  # ID del canal de bienvenida
    canal = member.guild.get_channel(canal_id)

    if canal:
        embed = discord.Embed(
            title="Bienvenida Servidor",
            description=f"¡Gracias! {member.mention} por unirte a **Jalisco | Mexico | Rp | Spanish**.\nVerifícate para poder rolear en el servidor.",
            color=discord.Color.green()
        )
        embed.set_footer(text="Administracion Jalisco.")
        embed.set_image(url="https://images-ext-1.discordapp.net/external/oZQpnNnwE3wUJ2QS0RrB6QPGwmDUD1Kpc6iIHZYFMo0/%3Fwidth%3D540%26height%3D405/https/images-ext-1.discordapp.net/external/irMHoMwCShaD-ikkEf_hZRRX19-eEMzJsABe2j3tI8c/%253Fcid%253D6c09b952j2s159t9sjv70v2jmrmycgonnzdqtf9iuj1a26q6%2526ep%253Dv1_gifs_search%2526rid%253D200w.gif%2526ct%253Dg/https/media4.giphy.com/media/aUMdOzbjmAy9G/200w.gif?width=300&height=225")

        await canal.send(embed=embed)

    # ====== Mensaje por DM ======
    try:
        await member.send(
            f"👋 Hola {member.name}, bienvenido a **Jalisco | Mexico | Rp | Spanish**.\n"
            f"No olvides verificarte para poder rolear."
        )
    except:
        pass

#-----------------------.votacion---------------------------

@bot.command()
async def votacion(ctx):
    embed = discord.Embed(
        title="🗳️ Votación Apertura del Servidor",
        description=(
            "La Administración de **Jalisco RP** quiere conocer la opinión de la comunidad.\n\n"
            "¿Deseas que el servidor abra sus puertas ahora?\n\n"
            "✅ **Sí** – Estoy listo para empezar a rolear.\n"
            "❌ **No** – Prefiero esperar un poco más.\n\n"
            "Tu participación es importante para el futuro del servidor."
        ),
        color=discord.Color.blue()
    )
    embed.set_image(url="https://images-ext-1.discordapp.net/external/nBGPgckl_2G0l_6q6rt44XpVbPOXxIXSK1zct4mr7UI/https/1.bp.blogspot.com/--NgSrkEA6uU/YDXmi_VCPGI/AAAAAAABBDQ/yoaDf-XkHX0uS2OOdf0K8v5DCbGkN4ZvACLcBGAsYHQ/w640-h360/giphy%25252B%2525283%252529.gif?width=600&height=338")
    embed.set_footer(text="Administración Jalisco")

    message = await ctx.send(content="@everyone", embed=embed)

    # Agregar reacciones para votar
    await message.add_reaction("✅")
    await message.add_reaction("❌")

#-----------------.abrirserver---------------------------------

@bot.command()
async def abrirserver(ctx):
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")  # Fecha y hora exacta

    embed = discord.Embed(
        title="Estado de Servidor",
        description="━━━━━━━━ 🚀(Servidor Abierto)🚀 ━━━━━━━━",
        color=discord.Color.blue()
    )

    embed.add_field(name="『🔴🟢』 Host:", value=ctx.author.mention, inline=False)
    embed.add_field(name="📅 Fecha:", value=fecha_actual, inline=False)
    embed.add_field(name="🔑 Codigo::", value="JaliscoRp", inline=False)
    embed.add_field(name="", value="El servidor está abierto, ¡nos vemos en rol", inline=False)

    embed.set_image(url="https://images-ext-1.discordapp.net/external/nBGPgckl_2G0l_6q6rt44XpVbPOXxIXSK1zct4mr7UI/https/1.bp.blogspot.com/--NgSrkEA6uU/YDXmi_VCPGI/AAAAAAABBDQ/yoaDf-XkHX0uS2OOdf0K8v5DCbGkN4ZvACLcBGAsYHQ/w640-h360/giphy%25252B%2525283%252529.gif?width=600&height=338")
    embed.set_footer(text="Administración Jalisco")

    # 👉 Solo un mensaje, con @everyone
    await ctx.send(content="@everyone", embed=embed)

#---------------------.cerrarserver---------------------------

@bot.command()
async def cerrarserver(ctx):
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")  # Fecha y hora exacta

    embed = discord.Embed(
        title="Estado de Servidor",
        description="━━━━━━━━ 🔒(Servidor Cerrado)🔒 ━━━━━━━━",
        color=discord.Color.red()
    )

    embed.add_field(name="『🔴🟢』 Host:", value=ctx.author.mention, inline=False)
    embed.add_field(name="📅 Fecha:", value=fecha_actual, inline=False)
    embed.add_field(name="💬 Mensaje:", value="El servidor se ha cerrado temporalmente.", inline=False)

    embed.set_footer(text="Administración Jalisco")

    # 👉 Solo un mensaje, con @everyone
    await ctx.send(content="@everyone", embed=embed)

# ====== /warn ======
@bot.tree.command(name="warn", description="Advertir a un usuario por incumplir reglas")
@app_commands.describe(
    usuario="Usuario que será advertido",
    razon="Motivo de la advertencia"
)
async def warn(interaction: discord.Interaction, usuario: discord.Member, razon: str):
    # Crear embed de advertencia
    embed = discord.Embed(
        title="⛔ | Advertencia",
        description="Persona advertida por romper una regla del servidor.",
        color=discord.Color.red()
    )
    embed.add_field(name="Usuario advertido:", value=usuario.mention, inline=False)
    embed.add_field(name="Razón:", value=razon, inline=False)
    embed.add_field(name="Staff:", value=interaction.user.mention, inline=False)
    embed.set_footer(text="Administración Jalisco")

    # Enviar embed al canal
    message = await interaction.response.send_message(embed=embed)
    # Obtener el mensaje real para poder reaccionar
    msg = await interaction.original_response()
    await msg.add_reaction("⁉️")

    # Enviar mensaje por DM al usuario advertido
    try:
        await usuario.send(
            f"⚠️ Has recibido una advertencia en **{interaction.guild.name}**.\n"
            f"**Motivo:** {razon}\n"
            f"**Staff:** {interaction.user.mention}\n\n"
            "Te pedimos que sigas las reglas para evitar sanciones más graves."
        )
    except:
        pass  # Si tiene los DMs cerrados, ignoramos el error

#---------------------- .autoroles---------------------------
@bot.command()
async def autoroles(ctx):
    embed = discord.Embed(
        title="🚦 Auto Roles Jalisco RP",
        description=(
            "Elige tu **trabajo** reaccionando con el emoji correspondiente.\n\n"
            "🚖 → **Taxista**\n"
            "💼 → **Abogado**\n"
            "🩸 → **Medicos**\n"
            "⚙️ → **Mecanicos**\n"
            "📺 → **Periodista**\n"
            "🚧 → **DOT**\n"
            "👨‍🚒 → **Bomberos**\n\n"
            "👉 Solo puedes tener **un rol a la vez**, si eliges otro se reemplazará."
        ),
        color=discord.Color.gold()
    )
    embed.set_footer(text="Administración Jalisco")

    message = await ctx.send(embed=embed)

    # Diccionario de emojis con ID de roles
    emojis_roles = {
        "🚖": 1177497391218303097,  # Taxista
        "💼": 1177497382888423454,  # Abogado
        "🩸": 1177497383618215959,  # Medicos
        "⚙️": 1177497389658026014,  # Mecanicos
        "📺": 1177497390647889992,  # Periodista
        "🚧": 1177497392602423356,  # DOT
        "👨‍🚒": 1177497386868805684  # Bomberos
    }

    for emoji in emojis_roles:
        await message.add_reaction(emoji)

    # Guardamos la info para manejar las reacciones
    bot.autoroles_message_id = message.id
    bot.autoroles_roles = emojis_roles


# Evento: cuando alguien reacciona
@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id != getattr(bot, "autoroles_message_id", None):
        return

    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)

    if not member or member.bot:
        return

    # Quitar cualquier rol anterior del sistema
    for role_id in bot.autoroles_roles.values():
        role = guild.get_role(role_id)
        if role in member.roles:
            await member.remove_roles(role)

    # Asignar el nuevo rol
    role_id = bot.autoroles_roles.get(str(payload.emoji))
    if role_id:
        role = guild.get_role(role_id)
        if role:
            await member.add_roles(role)


# Evento: cuando alguien quita la reacción (le quitamos el rol también)
@bot.event
async def on_raw_reaction_remove(payload):
    if payload.message_id != getattr(bot, "autoroles_message_id", None):
        return

    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)

    if not member or member.bot:
        return

    role_id = bot.autoroles_roles.get(str(payload.emoji))
    if role_id:
        role = guild.get_role(role_id)
        if role:
            await member.remove_roles(role)

#----------------------
from keep_alive import keep_alive

keep_alive()  # mantiene vivo el bot

bot.run(TOKEN)
