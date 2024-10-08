import io
from datetime import datetime

import disnake
from disnake.ext import commands

from src.utils import logger, main_db


class EventMessages(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        super(EventMessages, self).__init__()
        self.logger = logger
        self.settings_db = main_db
        self.bot = bot

    @commands.Cog.listener()
    async def on_thread_create(self, thread: disnake.Thread) -> None:
        logger_channel = await self.logger.get_loggers(
            guild_id=thread.guild.id, to_return="message"
        )

        if not logger_channel:
            return

        if thread.owner == thread.guild.me:
            return

        embed = disnake.Embed(
            color=self.settings_db.get_embed_color(thread.guild.id),
            title="Synth | Thread created",
            description="",
        )

        embed.add_field(name="Thread name", value=thread.name)
        embed.add_field(name="Thread channel", value=thread)
        embed.add_field(
            name="Thread author",
            value=f"{thread.owner.mention} (`{thread.owner}` `ID: {thread.owner_id}`)",
        )

        if channel := await thread.guild.fetch_channel(int(logger_channel)):
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread: disnake.Thread) -> None:
        logger_channel = await self.logger.get_loggers(
            guild_id=thread.guild.id, to_return="message"
        )

        if not logger_channel:
            return

        if thread.owner == thread.guild.me:
            return

        embed = disnake.Embed(
            color=self.settings_db.get_embed_color(thread.guild.id),
            title="Synth | Thread deleted",
            description="",
        )
        embed.add_field(name="Thread name", value=thread.name)
        embed.add_field(name="Thread channel", value=thread)
        embed.add_field(
            name="Thread author",
            value=f"{thread.owner.mention} (`{thread.owner}` `ID: {thread.owner_id}`)",
        )

        if channel := await thread.guild.fetch_channel(int(logger_channel)):
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: disnake.Message) -> None:
        logger_channel = await self.logger.get_loggers(
            guild_id=message.guild.id, to_return="message"
        )

        if not logger_channel:
            return

        if message.author == message.guild.me:
            return

        files = []
        embeds = []
        embed = disnake.Embed(
            color=self.settings_db.get_embed_color(message.guild.id),
            title="Synth | Deleted Message",
            description=None,
        )
        embed.add_field(name="Additional information", value="No information")
        field_dop_index = next(
            index
            for index, field in enumerate(embed.fields)
            if field.name == "Additional information"
        )
        embeds.append(embed)

        if len(message.content) > 1900:
            temp_file = io.StringIO()
            temp_file.write(message.content)
            temp_file.seek(0)
            files.append(
                disnake.File(
                    fp=io.BytesIO(temp_file.read().encode()), filename="message.txt"
                )
            )
            message.content = "See message.txt file"

        if message.attachments:
            for num, attachment in enumerate(message.attachments, start=1):
                embed.set_field_at(
                    field_dop_index,
                    name="Additional information",
                    value=f"Number of media files: `{num}`",
                )
                files.append(await attachment.to_file())

        if message.embeds:
            embed.set_field_at(
                field_dop_index,
                name="Additional information",
                value=f"Number of Embeds Deleted: `{len(message.embeds)}`",
            )
            for num, emb in enumerate(message.embeds, start=1):
                if num < 9:
                    emb.set_footer(text=f"Number: {num}")
                    embeds.append(emb)

        embed.add_field(
            name="Author",
            value=f"{message.author.mention} (`{message.author}` `ID: {message.author.id}`)",
            inline=False,
        )
        embed.add_field(
            name="Content",
            value=message.content,
            inline=False,
        )
        embed.add_field(
            name="Deleted at",
            value=disnake.utils.format_dt(datetime.now(), style="f"),
            inline=False,
        )
        embed.add_field(
            name="Channel",
            value=f"{message.channel.mention} (`ID: {message.channel.id}`)",
            inline=False,
        )
        embed.set_thumbnail(url=message.author.avatar)

        if channel := await message.guild.fetch_channel(int(logger_channel)):
            await channel.send(
                embeds=embeds, files=files if len(files) > 10 else files[:10]
            )
            if len(files) > 10:
                await channel.send(file=files[11])

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(
        self, payload: disnake.RawBulkMessageDeleteEvent
    ) -> None:
        if not payload.cached_messages:
            return

        logger_channel = await self.logger.get_loggers(
            guild_id=payload.guild_id, to_return="message"
        )

        if not logger_channel:
            return

        temp_file = io.StringIO()
        files = []
        embeds = []
        embed = disnake.Embed(
            color=self.settings_db.get_embed_color(payload.guild_id),
            title="Synth | Deleted Messages",
            description=None,
        )
        embed.add_field(name="Additional information", value="No information")
        embeds.append(embed)

        for message in payload.cached_messages:
            if message.author == message.guild.me:
                continue

            created_at = disnake.utils.format_dt(message.created_at, style="f")
            is_bot = "Yes" if message.author.bot else "No"
            embeds_info = []

            if message.attachments:
                for _, attachment in enumerate(message.attachments, start=1):
                    files.append(await attachment.to_file())

            if message.embeds:
                for num, embed in enumerate(message.embeds, start=1):
                    if num < 9:
                        embed.set_footer(text=f"Number: {num}")
                        fields = "\n".join(
                            [
                                f"{field.name}: {field.value}"
                                for field in embed.fields
                                if embed.fields
                            ]
                        )
                        embeds_info.append(
                            f"Number: {num}\nTitle: {embed.title}\nURL: {embed.url}"
                            f"\nDescription: {embed.description}"
                            f"\nFields:\n{fields}\nFooter: {embed.footer}"
                        )

            embeds = "\n".join(embeds_info)

            temp_file.write(
                f"Author: {message.author} ({message.author.id})"
                f"\nIs bot? {is_bot}"
                f"\nCreated at: {created_at}"
                f"\nContent: {message.content}\n"
                f"\nNumber of attachments: {len(message.attachments)}"
                f"\nNumber of embeds: {len(message.embeds)}"
                f"\nEmbeds info:\n{embeds}"
                f"\nChannel: {message.channel.name} ({message.channel.id})"
                f"\nDeleted at: {disnake.utils.format_dt(datetime.now(), style='f')}"
            )

        temp_file.seek(0)

        files.append(
            disnake.File(
                fp=io.BytesIO(temp_file.read().encode()), filename="message.txt"
            )
        )

        guild = await self.bot.fetch_guild(payload.guild_id)
        channel = await guild.fetch_channel(int(logger_channel))
        await channel.send(embeds=embeds)

        for file in range(0, len(files), 10):
            await channel.send(files=files[file : file + 10])

    @commands.Cog.listener()
    async def on_message_edit(
        self, before: disnake.Message, after: disnake.Message
    ) -> None:
        if before.author == before.guild.me:
            return

        if before.content == after.content:
            return

        logger_channel = await self.logger.get_loggers(
            guild_id=before.guild.id, to_return="message"
        )
        temp_file = None

        if not logger_channel:
            return

        if before.content == after.content:
            return

        if len(after.content) > 1900:
            temp_file = io.StringIO()
            temp_file.write(f"Before: {before.content}\n\nAfter: {after.content}")
            temp_file.seek(0)
            after.content = before.content = "See message.txt file"

        embed = disnake.Embed(
            title="Synth | Edited Message",
            description=(
                f"Before: {before.content}\nAfter: {after.content}"
                if len(after.content) <= 1900
                else after.content
            ),
            color=self.settings_db.get_embed_color(before.guild.id),
        )
        embed.add_field(
            name="Author",
            value=f"{after.author.mention} (`{after.author}` `ID: {after.author.id}`)",
            inline=False,
        )
        embed.add_field(
            name="Edited at",
            value=disnake.utils.format_dt(after.edited_at, style="f"),
            inline=True,
        )
        embed.add_field(
            name="Channel",
            value=f"{before.channel.mention} (`ID: {before.channel.id}`)",
        )
        channel = before.guild.get_channel(int(logger_channel))
        await channel.send(
            embed=embed,
            file=disnake.File(
                fp=io.BytesIO(temp_file.read().encode()), filename="message.txt"
            )
            if temp_file
            else None,
        )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(EventMessages(bot=bot))
