"""AI Bot"""
import asyncio
import logging

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class AIBot:
    """AI Bot"""
    def __init__(
            self,
            client: AsyncOpenAI,
            react_title_prompt: str = 'React funny to the nickname') -> None:

        self.react_title_prompt = react_title_prompt
        self.client = client

    async def rate_title(self, title: str):
        """Rate title"""
        return await self.completion(
            prompt=self.react_title_prompt,
            query=title)

    async def completion(self, prompt: str, query: str | None) -> str | None:
        """Get completion"""
        logger.info(
            '[openai completion request] prompt: %s, query: %s', prompt, query)

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


if __name__ == '__main__':
    # test bot
    from dotenv import load_dotenv

    logging.basicConfig(level=logging.DEBUG)

    load_dotenv()

    ai_bot = AIBot(client=AsyncOpenAI())

    # answer = asyncio.run(ai_bot.rate_title('Mister Streamer'))
    answer = asyncio.run(ai_bot.completion(
        'Ты рекламщик из игры GTA V RP, который рекламирует на улицах',
        'Коротко прорекламируй покупку титула в чате'
    ))

    print(answer)
