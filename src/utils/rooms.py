import disnake
from disnake.ext import commands

from src.utils import private_rooms, PrivateRoomsDatabase


class SetOwnerSelect(disnake.ui.UserSelect):
    def __init__(
        self,
        bot: commands.Bot,
        channel: disnake.VoiceChannel,
        voices: PrivateRoomsDatabase = private_rooms,
    ):
        self.bot = bot
        self.voices = voices
        self.channel = channel
        super().__init__(placeholder="Choose member", min_values=1, max_values=1)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.send_message(f"{self.values[0]}")
        if selected_users := self.values:
            result = self.voices.get_items_in_cache({"guild_id": inter.guild_id})
            for channel in result.get("channels"):
                if channel.get("channel_id") == self.channel.id:
                    if selected_users[0].id != channel.get("owner_id"):
                        embed = disnake.Embed(
                            title="Ownership transfer",
                            description=f"Successfully transferred ownership to {selected_users[0]}",
                            color=0x2F3236,
                        )
                        embed.set_footer(
                            text=f"Synth © 2023 | All Rights Reserved",
                            icon_url=self.bot.user.avatar,
                        )
                        await inter.channel.send(embed=embed)
                        return await self.voices.set_owner(
                            guild_id=inter.guild_id,
                            voice_channel=self.channel,
                            member=selected_users[0],
                        )
                    embed = disnake.Embed(
                        title="Ownership transfer",
                        description=f"<a:error:1168599839899144253> You are already the owner of the room",
                        color=disnake.Color.red(),
                    )
                    embed.set_footer(
                        text=f"Synth © 2023 | All Rights Reserved",
                        icon_url=self.bot.user.avatar,
                    )
                    return await inter.channel.send(embed=embed)


class AccessToChannelSelect(disnake.ui.UserSelect):
    def __init__(
        self,
        bot: commands.Bot,
        channel: disnake.VoiceChannel,
        voices: PrivateRoomsDatabase = private_rooms,
    ):
        self.bot = bot
        self.voices = voices
        self.channel = channel
        super().__init__(placeholder="Choose members", min_values=1, max_values=25)

    async def callback(self, inter: disnake.MessageInteraction):
        # await inter.response.send_message(f"{self.values[0]}")
        if selected_users := self.values:
            result = self.voices.get_items_in_cache({"guild_id": inter.guild_id})
            for channel in result.get("channels"):
                if channel.get("channel_id") == self.channel.id:
                    for user in selected_users:
                        if perms := self.channel.permissions_for(user):
                            await inter.channel.set_permissions(
                                user, connect=True if not perms.connect else False
                            )

                        embed = disnake.Embed(
                            title="Muted members",
                            description=f"Successfully {'gave' if not perms.connect else 'removed'} access to room "
                            f"for: **{user.mention}**",
                            color=0x2F3236,
                        )
                        embed.set_footer(
                            text=f"Synth © 2023 | All Rights Reserved",
                            icon_url=self.bot.user.avatar,
                        )
                        await inter.send(embed=embed, ephemeral=True)


class MuteUnmuteSelect(disnake.ui.Select):
    def __init__(
        self,
        bot: commands.Bot,
        channel: disnake.VoiceChannel,
        voices: PrivateRoomsDatabase = private_rooms,
    ):
        self.bot = bot
        self.voices = voices
        self.channel = channel

        options = []

        for member in channel.members:
            options.append(
                disnake.SelectOption(
                    label=member.name,
                    value=str(member.id),
                    emoji="<:unmute:1169690521472614500>"
                    if not member.voice.mute
                    else "<:mute:1170712518725992529>",
                )
            )

        super().__init__(
            placeholder="Choose members",
            min_values=1,
            max_values=len(channel.members),
            options=options,
        )

    async def callback(self, inter: disnake.MessageInteraction):
        result = self.voices.get_items_in_cache({"guild_id": inter.guild_id})
        for channel in result.get("channels"):
            if channel.get("channel_id") == self.channel.id:
                for member_id in self.values:
                    member = inter.guild.get_member(int(member_id))

                    await member.edit(
                        voice_channel=self.channel,
                        mute=True if not member.voice.mute else False,
                    )

                    mute_unmute = "unmuted" if not member.voice.mute else "muted"
                    embed = disnake.Embed(
                        title=f"{mute_unmute} members",
                        description=f"Successfully {mute_unmute}: **{member.mention}**",
                        color=0x2F3236,
                    )
                    embed.set_footer(
                        text=f"Synth © 2023 | All Rights Reserved",
                        icon_url=self.bot.user.avatar,
                    )
                    await inter.send(embed=embed, ephemeral=True)


class KickUsersSelect(disnake.ui.Select):
    def __init__(
        self,
        bot: commands.Bot,
        channel: disnake.VoiceChannel,
        voices: PrivateRoomsDatabase = private_rooms,
    ):
        self.bot = bot
        self.voices = voices
        self.channel = channel

        options = []

        for member in channel.members:
            options.append(
                disnake.SelectOption(
                    label=member.name,
                    value=str(member.id),
                    emoji="<:kick:1170712514288435271>",
                )
            )

        super().__init__(
            placeholder="Choose members",
            min_values=1,
            max_values=len(channel.members),
            options=options,
        )

    async def callback(self, inter: disnake.MessageInteraction):
        result = self.voices.get_items_in_cache({"guild_id": inter.guild_id})
        for channel in result.get("channels"):
            if channel.get("channel_id") == self.channel.id:
                for _ in self.values:
                    member = inter.guild.get_member(int(self.values[0]))
                    if member.voice.channel == self.channel:
                        await member.move_to(channel=None)  # type: ignore
                await inter.send("Successfully", ephemeral=True)


class SetChannelName(disnake.ui.Modal):
    def __init__(
        self,
        bot: commands.Bot,
        channel: disnake.VoiceChannel,
    ):
        self.bot = bot
        self.channel = channel
        self.values = {}

        super().__init__(
            title="Enter the new room name",
            components=[
                disnake.ui.TextInput(
                    label="Room name",
                    custom_id="channel_name",
                    placeholder="Enter the new room name",
                    required=True,
                ),
            ],
        )

    async def callback(self, inter: disnake.MessageInteraction):
        new_channel_name = inter.data["components"][0]["components"][0]["value"]
        await self.channel.edit(name=new_channel_name)

        embed = disnake.Embed(
            title="Changing the room name",
            description=f"Successfully changed the room name to: **{new_channel_name}**",
            color=0x2F3236,
        )
        embed.set_footer(
            text=f"Synth © 2023 | All Rights Reserved",
            icon_url=self.bot.user.avatar,
        )
        await inter.send(embed=embed, ephemeral=True)


class SetUserLimit(disnake.ui.Modal):
    def __init__(
        self,
        bot: commands.Bot,
        channel: disnake.VoiceChannel,
    ):
        self.bot = bot
        self.channel = channel
        self.values = {}

        super().__init__(
            title="Enter the new room user limit",
            components=[
                disnake.ui.TextInput(
                    label="Room user limit",
                    custom_id="channel_limit",
                    placeholder="Enter the new room user limit",
                    required=True,
                ),
            ],
        )

    async def callback(self, inter: disnake.MessageInteraction):
        new_channel_limit = inter.data["components"][0]["components"][0]["value"]
        await self.channel.edit(user_limit=int(new_channel_limit))

        embed = disnake.Embed(
            title="Changing the user limit",
            description=f"Successfully changed the room user limit to: **{new_channel_limit}**",
            color=0x2F3236,
        )
        embed.set_footer(
            text=f"Synth © 2023 | All Rights Reserved",
            icon_url=self.bot.user.avatar,
        )
        await inter.send(embed=embed, ephemeral=True)


class Buttons(disnake.ui.View):
    def __init__(
        self,
        bot: commands.Bot,
        author: disnake.Member,
        channel: disnake.VoiceChannel,
        voices: PrivateRoomsDatabase = private_rooms,
    ):
        super().__init__()
        self.bot = bot
        self.author = author
        self.voices = voices
        self.channel = channel

    @disnake.ui.button(emoji="<:store:1169690541986959464>")
    async def pen_callback(
        self, _: disnake.ui.button, interaction: disnake.MessageInteraction
    ):
        modal = SetChannelName(bot=self.bot, channel=self.channel)
        await interaction.response.send_modal(modal)

    @disnake.ui.button(emoji="<:members:1169684583369949285>", row=0)
    async def _users(
        self, _: disnake.ui.button, interaction: disnake.MessageInteraction
    ):
        modal = SetUserLimit(bot=self.bot, channel=self.channel)
        await interaction.response.send_modal(modal)

    @disnake.ui.button(emoji="<:list:1169690529643114547>", row=0)
    async def _unlock_slot(
        self, _: disnake.ui.button, interaction: disnake.MessageInteraction
    ):
        await self.channel.edit(user_limit=0)
        embed = disnake.Embed(
            title="Removing the user limit",
            description="Successfully removed the user limit for this channel.",
            color=0x2F3236,
        )
        embed.set_footer(
            text=f"Synth © 2023 | All Rights Reserved",
            icon_url=self.bot.user.avatar,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @disnake.ui.button(emoji="<:invite:1169690514430382160>", row=0)
    async def _lock_unlock(
        self, _: disnake.ui.button, interaction: disnake.MessageInteraction
    ):
        if perms := self.channel.permissions_for(interaction.guild.default_role):
            embed = disnake.Embed(
                title="Lock/Unlock the room",
                description=f"Successfully {'locked' if perms.connect else 'unlocked'} this channel for everyone.",
                color=0x2F3236,
            )
            embed.set_footer(
                text=f"Synth © 2023 | All Rights Reserved",
                icon_url=self.bot.user.avatar,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            result = await self.voices.get_owner_id(interaction.guild.id, self.channel)
            owner = interaction.guild.get_member(result)

            await self.channel.set_permissions(
                interaction.guild.default_role, connect=False if perms.connect else True
            )
            await self.channel.set_permissions(owner, connect=True)

    # noinspection SqlNoDataSourceInspection
    @disnake.ui.button(emoji="<:ban:1170712517308317756>", row=1)
    async def _kick(
        self, _: disnake.ui.button, interaction: disnake.MessageInteraction
    ):
        view = disnake.ui.View()

        view.add_item(
            KickUsersSelect(self.bot, channel=self.channel, voices=self.voices)
        )

        result = await self.voices.get_owner_id(interaction.guild.id, self.channel)
        owner = interaction.guild.get_member(result)

        embed = disnake.Embed(
            title="Disconnecting users",
            description="Select users for disconnecting from your private room",
            color=0x2F3236,
        )
        embed.add_field(
            name="Settings",
            value=(
                f"Owner: {owner.mention}\n"
                f"Name: **{self.channel.name}** ({self.channel.mention})\n"
                f"Limit: **{self.channel.user_limit}**\n"
                f"Bitrate: **{self.channel.bitrate}**"
            ),
        )
        embed.set_footer(
            text=f"Synth © 2023 | All Rights Reserved",
            icon_url=self.bot.user.avatar,
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @disnake.ui.button(emoji="<:hammer:1169685339720384512>", row=1)
    async def _access(
        self, _: disnake.ui.button, interaction: disnake.MessageInteraction
    ):
        view = disnake.ui.View()

        view.add_item(
            AccessToChannelSelect(self.bot, channel=self.channel, voices=self.voices)
        )

        result = await self.voices.get_owner_id(interaction.guild.id, self.channel)
        owner = interaction.guild.get_member(result)

        embed = disnake.Embed(
            title="Toggle users joining",
            description="Select users to allow/disallow to join the room",
            color=0x2F3236,
        )
        embed.add_field(
            name="Settings",
            value=(
                f"Owner: {owner.mention}\n"
                f"Name: **{self.channel.name}** ({self.channel.mention})\n"
                f"Limit: **{self.channel.user_limit}**\n"
                f"Bitrate: **{self.channel.bitrate}**"
            ),
        )
        embed.set_footer(
            text=f"Synth © 2023 | All Rights Reserved",
            icon_url=self.bot.user.avatar,
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @disnake.ui.button(emoji="<:mute:1170712518725992529>", row=1)
    async def _mute(
        self, _: disnake.ui.button, interaction: disnake.MessageInteraction
    ):
        view = disnake.ui.View()
        view.add_item(MuteUnmuteSelect(self.bot, channel=self.channel))

        result = await self.voices.get_owner_id(interaction.guild.id, self.channel)
        owner = interaction.guild.get_member(result)

        embed = disnake.Embed(
            title="Toggle users microphone",
            description="Select users to mute/unmute in your room",
            color=0x2F3236,
        )
        embed.add_field(
            name="Settings",
            value=(
                f"Owner: {owner.mention}\n"
                f"Name: **{self.channel.name}** ({self.channel.mention})\n"
                f"Limit: **{self.channel.user_limit}**\n"
                f"Bitrate: **{self.channel.bitrate}**"
            ),
        )
        embed.set_footer(
            text=f"Synth © 2023 | All Rights Reserved",
            icon_url=self.bot.user.avatar,
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @disnake.ui.button(emoji="<:owner:1169684595697004616>", row=1)
    async def transfer_ownership(
        self, _: disnake.ui.button, interaction: disnake.MessageInteraction
    ):
        view = disnake.ui.View()

        view.add_item(SetOwnerSelect(self.bot, channel=self.channel))

        result = await self.voices.get_owner_id(interaction.guild.id, self.channel)
        owner = interaction.guild.get_member(result)

        embed = disnake.Embed(
            title="Transfer ownership",
            description="Select a user to transfer the ownership of the room",
            color=0x2F3236,
        )
        embed.add_field(
            name="Settings",
            value=f"Owner: {owner.mention}\n"
            f"Name: **{self.channel.name}** ({self.channel.mention})\n"
            f"Limit: **{self.channel.user_limit}**\n"
            f"Bitrate: **{self.channel.bitrate}**",
        )
        embed.set_footer(
            text=f"Synth © 2023 | All Rights Reserved",
            icon_url=self.bot.user.avatar,
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if info := self.voices.get_items_in_cache({"guild_id": self.channel.guild.id}):
            for channel in info.get("channels"):
                if channel.get("channel_id") == self.channel.id:
                    if interaction.author.id != channel.get("owner_id"):
                        embed = disnake.Embed(
                            description="<a:error:1168599839899144253> You are not allowed to use this buttons",
                            color=disnake.Color.red(),
                        )
                        await interaction.response.send_message(
                            embed=embed, ephemeral=True
                        )
                        return False
            return True
