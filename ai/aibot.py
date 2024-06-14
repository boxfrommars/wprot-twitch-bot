"""AI Bot"""
import asyncio
import logging
import os
from string import Template

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class AIBot:
    """AI Bot"""
    def __init__(
            self,
            client: AsyncOpenAI,
            prompts: dict) -> None:

        self.prompts = prompts
        self.client = client

    async def rate_title(self, title: str):
        """Rate title"""
        return await self.completion(
            prompt=self.prompts.get('REACT_TITLE_PROMPT', ''),
            query=title)

    async def completion(self, prompt: str, query: str) -> str | None:
        """Get completion"""
        logger.info(
            '[openai completion request] prompt: %s, query: %s', prompt, query)

        if not prompt or not query:
            logger.warning(
                '[openai completion request]  Missing prompt or query')
            return None

        completion = await self.client.chat.completions.create(
            model='gpt-4o',
            messages=[{
                "role": "system",
                "content": prompt
            }, {
                'role': 'user',
                'content': query
            }]
        )
        if completion.choices:
            completion_result = completion.choices[0].message.content
            logger.info(
                '[openai completion response] %s', completion_result)

            return completion_result

        return None

    async def advert_title(self, game_name: str | None) -> str | None:
        """Advert title"""
        data = {'game_name': game_name}
        if game_name and (game_name not in ['Just Chatting']):
            prompt_tmpl = Template(self.prompts.get('AD_IN_GAME_PROMPT', ''))
            query = self.prompts.get('AD_IN_GAME_QUERY', '')
        else:
            prompt_tmpl = Template(self.prompts.get('AD_NO_GAME_PROMPT', ''))
            query = self.prompts.get('AD_NO_GAME_QUERY', '')

        ads = await self.completion(prompt_tmpl.substitute(data), query)
        if ads:
            ads_template = Template(self.prompts.get('AD_TEMPLATE', '$ads'))
            ads = ads_template.substitute({'ads': ads})
            logger.info('[advert] %s', ads)

            return ads

        return None


if __name__ == '__main__':
    # test bot
    from dotenv import load_dotenv

    load_dotenv()

    logging.basicConfig(level=logging.INFO)

    bot_prompts = {}
    for prompt_key in [
        'REACT_TITLE_PROMPT', 'AD_IN_GAME_PROMPT', 'AD_IN_GAME_QUERY',
        'AD_NO_GAME_PROMPT', 'AD_NO_GAME_QUERY', 'AD_TEMPLATE'
    ]:
        bot_prompts[prompt_key] = os.getenv(prompt_key, '')

    ai_bot = AIBot(client=AsyncOpenAI(), prompts=bot_prompts)
    # answer = asyncio.run(ai_bot.rate_title('Mister Streamer'))
    answer = asyncio.run(ai_bot.advert_title('Grand Theft Auto V'))
