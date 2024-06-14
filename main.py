"""WprotBot"""
import logging
import os

from openai import AsyncOpenAI
from twitchio import (  # type: ignore
    Message, PartialUser, PartialChatter)
from twitchio.ext import commands, routines  # type: ignore
from dotenv import load_dotenv

from ai.aibot import AIBot
from title_manager import TitleManager


logger = logging.getLogger(__name__)


class Bot(commands.Bot):
    """WprotBot"""
    def __init__(  # pylint: disable=too-many-arguments
            self,
            reward_id: str,
            access_token: str,
            channels: list,
            title_manager: TitleManager,
            ai_bot: AIBot | None = None) -> None:
        """
        Initialise the Bot
        """
        self.title_reward_id = reward_id
        self.token = access_token
        self.title_manager = title_manager
        self.ai_bot = ai_bot

        super().__init__(
            token=self.token,
            prefix='!',
            initial_channels=channels)

    async def event_ready(self) -> None:
        """
        Bot logged in. Connect to db and instantiate title manager
        """
        logger.info('Logged in as | %s [%s]', self.nick, self.user_id)
        await self.title_manager.up()

        self.advertise.start()  # pylint: disable=no-member

    async def event_message(self, message: Message) -> None:

        logger.info(
            '[msg %s] %s',
            message.author.name if message.author else None,
            message.content)

        if message.echo:  # ignore messages sent by the bot
            return
        if self.title_manager is None:  # something wrong (for mypy...)
            return

        if self.is_reward_message(message):
            # Save title for user if the reward message
            await self.title_manager.set_title(message.content, message.author)

            if self.ai_bot:
                ai_rate = await self.ai_bot.rate_title(message.content)
                if ai_rate:
                    logger.info('[title react] %s', ai_rate)
                    ai_rate = f'@{message.author.name} {ai_rate}'
                    await message.channel.send(ai_rate[:499])
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

    @routines.routine(minutes=30, wait_first=True)
    async def advertise(self):
        """Advertise title purchases"""

        broadcaster = await self.connected_channels[0].user()
        streams = await self.fetch_streams(user_ids=[broadcaster.id])
        if streams:
            stream = streams[0]
            logger.info(
                ('[advert needed] id: %s, game: %s, title: %s, started: %s, '
                 'tags: %s, type: %s'),
                stream.id, stream.game_name, stream.title, stream.started_at,
                stream.tags, stream.type
            )
            advertisement = await self.ai_bot.advert_title(stream.game_name)
            logger.info('[advert] %s', advertisement)
            if advertisement:
                await self.connected_channels[0].send(advertisement)
        else:
            logger.info('[advert] No stream')

    @commands.command()
    async def tit(
            self,
            ctx: commands.Context,
            action: str | None = 'info',
            user: PartialChatter | None = None) -> None:
        """Get title info or delete title"""

        logger.info(
            '[command tit] action: %s, user: %s, caller: %s, is_mod: %s',
            action,
            user.name if user else None,
            ctx.author.name if ctx.author else None,
            ctx.author.is_mod)

        if action not in ['info', 'delete']:
            return

        # moderators can manage users title
        if not (user and ctx.author.is_mod):
            user = ctx.author

        title_record = await self.title_manager.get_title(user)

        if title_record is None:  # do nothing if no title for the user
            logger.info('no title for %s', user.name)
            return

        logger.info('[title] %s', dict(title_record))

        if action == 'delete':
            await self.title_manager.delete_title(user)
            logger.info(
                '[delete title] user: %s, caller: %s',
                user.name, ctx.author.name)
            await ctx.send(f'@{user.name}, ваш титул удалён!')
        else:
            # show info
            logger.info(
                '[title info] %s: %s',
                user.name, title_record['title'])
            await ctx.send(self.title_manager.format_title_info(title_record))

    async def close(self):
        """
        Close database connection before bot shutdown
        """
        await self.title_manager.close()
        await super().close()

    async def announce(self, broadcaster: PartialUser, content: str):
        """Send announcement to the broadcaster channel"""
        logger.info('[announce] %s', content)

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

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s : %(name)s : %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S %z")

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
        template=os.getenv('GREETING_TEMPLATE', '{title} @{username}'),
        cooldown=int(os.getenv('TITLE_COOLDOWN_SEC', '21600')),
        lifetime=int(os.getenv('TITLE_LIFETIME_SEC', '1209600')),
    )

    is_ai_enabled = os.getenv('IS_AI_ENABLED', '').lower() == 'true'

    prompts = {}
    for prompt_key in [
        'REACT_TITLE_PROMPT', 'AD_IN_GAME_PROMPT', 'AD_IN_GAME_QUERY',
        'AD_NO_GAME_PROMPT', 'AD_NO_GAME_QUERY', 'AD_TEMPLATE'
    ]:
        prompts[prompt_key] = os.getenv(prompt_key, '')

    aibot = AIBot(client=AsyncOpenAI(),
                  prompts=prompts) if is_ai_enabled else None

    bot = Bot(
        reward_id=title_reward_id,
        access_token=bot_access_token,
        channels=[bot_channel],
        title_manager=bot_title_manager,
        ai_bot=aibot
    )
    bot.run()
