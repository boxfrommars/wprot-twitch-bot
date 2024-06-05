"""Wprot Bot"""
import os
from asyncio import sleep
from sqlite3 import Row
import aiosqlite
from twitchio import Message  # type: ignore
from twitchio.ext import commands  # type: ignore
from dotenv import load_dotenv

from title_manager import TitleManager


class Bot(commands.Bot):
    """WprotBot"""
    def __init__(self, greeting_template: str = '{title} вошёл в чат') -> None:
        """
        Initialise the Bot
        """
        self.title_reward_id = os.getenv('REWARD_ID')
        self.greeting_template = greeting_template

        # we cannot create connection outside async
        self.db: aiosqlite.Connection | None = None
        self.title_manager: TitleManager | None = None

        super().__init__(
            token=os.getenv('ACCESS_TOKEN'),
            prefix='!',
            initial_channels=['boxfrommars'])

    async def event_ready(self) -> None:
        """
        Bot logged in. Connect to db and instantiate title manager
        """
        print(f'Logged in as | {self.nick} [{self.user_id}]')

        self.db = await aiosqlite.connect(str(os.getenv('DB_NAME')))
        self.db.row_factory = Row

        self.title_manager = TitleManager(self.db, cooldown=5)
        await self.title_manager.up()

    async def event_message(self, message: Message) -> None:
        if message.echo:  # ignore messages sent by the bot
            return
        if self.title_manager is None:  # something wrong with db (for mypy...)
            return

        print(f'{message.content} [{message.author.name} {message.timestamp}]')

        if self.is_reward_message(message):
            # Save title for user if the reward message
            await self.title_manager.set_title(message.content, message.author)
        else:
            # The title record if purchased, otherwise None.
            title_record = await self.title_manager.get_title(message.author)

            if title_record is not None:
                # Title was purchased,
                # so update last posted time (for cooldown check)
                await self.title_manager.update_last_posted_at(message.author)

                # Greeting is needed (subscription is active and cooldown)
                if self.title_manager.is_greeting_needed(title_record):
                    # format greeting
                    greeting = self.greeting_template.format(**title_record)

                    await sleep(1)
                    await message.channel.send(greeting)

        await self.handle_commands(message)

    @commands.command()
    async def hello(self, ctx: commands.Context) -> None:
        """
        Test command. Send a hello back!
        """
        print('Hello command received')
        await sleep(1)
        await ctx.send(f'Hello {ctx.author.name}!')

    async def close(self):
        """
        Close database connection before bot close
        """
        if self.db:
            await self.db.commit()
            await self.db.close()

        await super().close()

    def is_reward_message(self, message: Message) -> bool:
        """Check that message is the reward"""
        return message.tags \
            and message.tags.get('custom-reward-id') == self.title_reward_id


def main() -> None:
    """Run bot"""
    load_dotenv()

    bot = Bot()
    bot.run()


if __name__ == '__main__':
    main()
