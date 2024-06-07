"""WprotBot"""
import os
from twitchio import (  # type: ignore
    Message, PartialUser, PartialChatter)
from twitchio.ext import commands  # type: ignore
from dotenv import load_dotenv

from title_manager import TitleManager


class Bot(commands.Bot):
    """WprotBot"""
    def __init__(
            self,
            reward_id: str,
            access_token: str,
            channels: list,
            title_manager: TitleManager) -> None:
        """
        Initialise the Bot
        """
        self.title_reward_id = reward_id
        self.token = access_token
        self.title_manager = title_manager

        super().__init__(
            token=self.token,
            prefix='!',
            initial_channels=channels)

    async def event_ready(self) -> None:
        """
        Bot logged in. Connect to db and instantiate title manager
        """
        print(f'Logged in as | {self.nick} [{self.user_id}]')
        await self.title_manager.up()

    async def event_message(self, message: Message) -> None:
        if message.echo:  # ignore messages sent by the bot
            return
        if self.title_manager is None:  # something wrong (for mypy...)
            return

        print(f'[{message.author.name} {message.timestamp}] {message.content}')

        if self.is_reward_message(message):
            # Save title for user if the reward message
            await self.title_manager.set_title(message.content, message.author)
        else:
            # The title record if purchased, None otherwise.
            title_record = await self.title_manager.get_title(message.author)

            if title_record is not None:
                # Title was purchased,
                # so update last posted time (for cooldown check)
                await self.title_manager.update_last_posted_at(message.author)

                # Greeting is needed (active subscription and proper cooldown)
                if self.title_manager.is_greeting_needed(title_record):
                    greeting = self.title_manager.greeting(title_record)
                    broadcaster = await message.channel.user()

                    await self.announce(broadcaster, greeting)

        await self.handle_commands(message)

    @commands.command()
    async def title(
            self,
            ctx: commands.Context,
            action: str | None,
            user: PartialChatter | None) -> None:
        """Get title info or delete title"""

        # moderators can
        if not (user and ctx.author.is_mod):
            user = ctx.author

        title_record = await self.title_manager.get_title(user)

        if title_record is None:  # do nothing if no title for the user
            return

        if action == 'delete':
            await self.title_manager.delete_title(user)
            await ctx.send(f'@{user.name}, ваш титул удалён!')
        else:
            # show info
            await ctx.send(self.title_manager.format_title_info(title_record))

    async def close(self):
        """
        Close database connection before bot shutdown
        """
        await self.title_manager.close()
        await super().close()

    async def announce(self, broadcaster: PartialUser, content: str):
        """Send announcement to the broadcaster channel"""
        await broadcaster.chat_announcement(
            token=self.token,
            moderator_id=str(self.user_id),
            message=content,
            color='green'
        )

    def is_reward_message(self, message: Message) -> bool:
        """Check the message for the reward"""
        return message.tags \
            and message.tags.get('custom-reward-id') == self.title_reward_id


if __name__ == '__main__':
    load_dotenv()

    title_reward_id = os.getenv('REWARD_ID')
    bot_access_token = os.getenv('ACCESS_TOKEN')
    bot_channel = os.getenv('CHANNEL')

    if not (title_reward_id and bot_access_token and bot_channel):
        raise KeyError(
            'Missing some enviroment variables '
            '(REWARD_ID or ACCESS_TOKEN or CHANNEL) '
            'You should add them to .env file')

    # @TODO use a connection instead of db_name
    bot_title_manager = TitleManager(
        db_name=os.getenv('DB_NAME', 'wprotbot.db'),
        template=os.getenv('GREETING_TEMPLATE',
                           '{title} @{username} has joined the chat!'),
        cooldown=int(os.getenv('TITLE_COOLDOWN_SEC', '21600')),
        lifetime=int(os.getenv('TITLE_LIFETIME_SEC', '1209600')),
    )

    bot = Bot(
        reward_id=title_reward_id,
        access_token=bot_access_token,
        channels=[bot_channel],
        title_manager=bot_title_manager
    )
    bot.run()
