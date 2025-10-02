import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime, timezone
from aiohttp import web
import asyncio

# --------------------------
# Token Setup
# --------------------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")  # Set this in Render environment variables

# --------------------------
# Bot Setup
# --------------------------
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

LOG_CHANNEL_ID = 1417049521845698580


# --------------------------
# Universal Logger Function
# --------------------------
async def log_event(
    title: str,
    description: str,
    color: discord.Color,
    guild: discord.Guild,
    actor=None,
    target=None,
):
    try:
        channel = bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title=title,
                description=description,
                color=color,
                timestamp=datetime.now(timezone.utc),  # Fixed UTC deprecation
            )
            if actor:
                embed.add_field(name="👤 Action By", value=str(actor), inline=False)
            if target:
                embed.add_field(name="🎯 Target", value=str(target), inline=False)
            embed.set_footer(text=f"Server: {guild.name}")
            await channel.send(embed=embed)
    except Exception as e:
        print(f"[ERROR] Failed to send log: {e}")


# --------------------------
# Bot Ready
# --------------------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")


# --------------------------
# Member Events
# --------------------------
@bot.event
async def on_member_join(member):
    try:
        if member.bot:
            async for entry in member.guild.audit_logs(
                limit=1, action=discord.AuditLogAction.bot_add
            ):
                await log_event(
                    "🤖 Bot Added",
                    f"{member.mention} added to server.",
                    discord.Color.blurple(),
                    member.guild,
                    actor=entry.user,
                    target=member,
                )
                return
        await log_event(
            "📥 Member Joined",
            f"{member} joined the server.",
            discord.Color.green(),
            member.guild,
            target=member,
        )
    except Exception as e:
        print(f"[ERROR] on_member_join: {e}")


@bot.event
async def on_member_remove(member):
    try:
        guild = member.guild
        async for entry in guild.audit_logs(
            limit=1, action=discord.AuditLogAction.kick
        ):
            if entry.target.id == member.id:
                await log_event(
                    "👢 Member Kicked",
                    f"{member} was kicked by {entry.user.mention}.",
                    discord.Color.orange(),
                    guild,
                    actor=entry.user,
                    target=member,
                )
                return
        await log_event(
            "📤 Member Left",
            f"{member} left the server.",
            discord.Color.yellow(),
            guild,
            target=member,
        )
    except Exception as e:
        print(f"[ERROR] on_member_remove: {e}")


@bot.event
async def on_member_ban(guild, user):
    try:
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            await log_event(
                "⛔ Member Banned",
                f"{user} was banned.",
                discord.Color.red(),
                guild,
                actor=entry.user,
                target=user,
            )
            return
    except Exception as e:
        print(f"[ERROR] on_member_ban: {e}")


@bot.event
async def on_member_unban(guild, user):
    try:
        async for entry in guild.audit_logs(
            limit=1, action=discord.AuditLogAction.unban
        ):
            await log_event(
                "✅ Member Unbanned",
                f"{user} was unbanned.",
                discord.Color.green(),
                guild,
                actor=entry.user,
                target=user,
            )
            return
    except Exception as e:
        print(f"[ERROR] on_member_unban: {e}")


@bot.event
async def on_member_update(before, after):
    try:
        before_timeout = getattr(before, "communication_disabled_until", None)
        after_timeout = getattr(after, "communication_disabled_until", None)

        if before_timeout != after_timeout:
            if after_timeout:
                await log_event(
                    "🔇 Timeout Applied",
                    f"{after} muted until {after_timeout}.",
                    discord.Color.purple(),
                    after.guild,
                    target=after,
                )
            else:
                await log_event(
                    "🔊 Timeout Removed",
                    f"Timeout removed for {after}.",
                    discord.Color.green(),
                    after.guild,
                    target=after,
                )
    except Exception as e:
        print(f"[ERROR] on_member_update: {e}")


# --------------------------
# Channel Events
# --------------------------
@bot.event
async def on_guild_channel_create(channel):
    try:
        async for entry in channel.guild.audit_logs(
            limit=1, action=discord.AuditLogAction.channel_create
        ):
            await log_event(
                "📌 Channel Created",
                f"{channel.mention} created.",
                discord.Color.green(),
                channel.guild,
                actor=entry.user,
                target=channel,
            )
    except Exception as e:
        print(f"[ERROR] on_guild_channel_create: {e}")


@bot.event
async def on_guild_channel_delete(channel):
    try:
        async for entry in channel.guild.audit_logs(
            limit=1, action=discord.AuditLogAction.channel_delete
        ):
            await log_event(
                "❌ Channel Deleted",
                f"{channel.name} deleted.",
                discord.Color.red(),
                channel.guild,
                actor=entry.user,
                target=channel,
            )
    except Exception as e:
        print(f"[ERROR] on_guild_channel_delete: {e}")


# --------------------------
# Role Events
# --------------------------
@bot.event
async def on_guild_role_create(role):
    try:
        async for entry in role.guild.audit_logs(
            limit=1, action=discord.AuditLogAction.role_create
        ):
            await log_event(
                "🆕 Role Created",
                f"Role `{role.name}` created.",
                discord.Color.green(),
                role.guild,
                actor=entry.user,
                target=role,
            )
    except Exception as e:
        print(f"[ERROR] on_guild_role_create: {e}")


@bot.event
async def on_guild_role_delete(role):
    try:
        async for entry in role.guild.audit_logs(
            limit=1, action=discord.AuditLogAction.role_delete
        ):
            await log_event(
                "❌ Role Deleted",
                f"Role `{role.name}` deleted.",
                discord.Color.red(),
                role.guild,
                actor=entry.user,
                target=role,
            )
    except Exception as e:
        print(f"[ERROR] on_guild_role_delete: {e}")


# --------------------------
# Invite Events
# --------------------------
@bot.event
async def on_invite_create(invite):
    try:
        async for entry in invite.guild.audit_logs(
            limit=1, action=discord.AuditLogAction.invite_create
        ):
            await log_event(
                "🔗 Invite Created",
                f"Invite `{invite.code}` created.",
                discord.Color.blue(),
                invite.guild,
                actor=entry.user,
            )
    except Exception as e:
        print(f"[ERROR] on_invite_create: {e}")


@bot.event
async def on_invite_delete(invite):
    try:
        async for entry in invite.guild.audit_logs(
            limit=1, action=discord.AuditLogAction.invite_delete
        ):
            await log_event(
                "❌ Invite Deleted",
                f"Invite `{invite.code}` deleted.",
                discord.Color.red(),
                invite.guild,
                actor=entry.user,
            )
    except Exception as e:
        print(f"[ERROR] on_invite_delete: {e}")


# --------------------------
# Message Events
# --------------------------
@bot.event
async def on_message_delete(message):
    try:
        if not message.author.bot:
            await log_event(
                "🗑️ Message Deleted",
                f"From {message.author.mention} in {message.channel.mention}:\n```{message.content}```",
                discord.Color.red(),
                message.guild,
                target=message.author,
            )
    except Exception as e:
        print(f"[ERROR] on_message_delete: {e}")


@bot.event
async def on_message_edit(before, after):
    try:
        if not before.author.bot and before.content != after.content:
            await log_event(
                "✏️ Message Edited",
                f"In {before.channel.mention}\n**Before:** {before.content}\n**After:** {after.content}",
                discord.Color.orange(),
                before.guild,
                target=before.author,
            )
    except Exception as e:
        print(f"[ERROR] on_message_edit: {e}")


# --------------------------
# aiohttp keep-alive server for Render Web Service
# --------------------------
async def handle(request):
    return web.Response(text="Bot is running!")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000)))
    await site.start()


# --------------------------
# Run Bot + Web Server
# --------------------------
async def main():
    await start_web_server()  # Start aiohttp server
    await bot.start(TOKEN)  # Start Discord bot


asyncio.run(main())
