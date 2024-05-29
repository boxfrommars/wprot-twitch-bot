"""Wprot Bot"""
import os
from twitchio.ext import commands
from dotenv import load_dotenv


class Bot(commands.Bot):
    """Wprot Bot"""
    def __init__(self):
        """
        Initialise our Bot with our access token, prefix
        and a list of channels to join on boot...
        """
        load_dotenv()
        access_token = os.getenv('ACCESS_TOKEN')
        super().__init__(
            token=access_token,
            prefix='!',
            initial_channels=['boxfrommars'])

    async def event_ready(self):
        """
        Notify us when everything is ready!
        We are logged in and ready to chat and use commands...
        """
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')

    @commands.command()
    async def hello(self, ctx: commands.Context):
        """
        Here we have a command hello, we can invoke our command with
        our prefix and command name e.g ?hello
        """
        # Send a hello back!
        # Sending a reply back to the channel is easy... Below is an example.
        await ctx.send(f'Hello {ctx.author.name}!')


bot = Bot()
bot.run()
# bot.run() is blocking and will stop execution of any below code
# here until stopped or closed.
