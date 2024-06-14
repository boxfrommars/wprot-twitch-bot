"""AI Bot"""
import asyncio
import logging

from openai import AsyncOpenAI
from twitchio import Stream  # type: ignore

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

    async def completion(self, prompt: str, query: str) -> str | None:
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

    async def advert_title(self, stream: Stream) -> str | None:
        """Advert title"""
        if stream.game_name and (stream.game_name not in ['Just Chatting']):
            ads = await self.completion(
                f'Ты герой игры {stream.game_name}',
                ('Коротко и смешно прорекламируй покупку титула на стриме '
                 'этой игры')
            )
        else:
            ads = await self.completion(
                'Ты милая добрая девочка, которая любит Эдгара',
                ('Коротко и смешно прорекламируй покупку титула у него '
                 'на стриме')
            )

        if ads:
            ads += ' (Титул можно купить за баллы канала)'

            logger.info(
                ('[advert] id: %s, game: %s, title: %s, started: %s, '
                 'tags: %s, type: %s, ads: %s'),
                stream.id, stream.game_name, stream.title, stream.started_at,
                stream.tags, stream.type, ads
            )

            return ads

        return None


if __name__ == '__main__':
    # test bot
    from dotenv import load_dotenv
    from collections import defaultdict

    logging.basicConfig(level=logging.INFO)

    load_dotenv()

    ai_bot = AIBot(client=AsyncOpenAI())

    stream_data = defaultdict(str, {
        'id': 1,
        'user_id': 2,
        'started_at': '2024-07-14 14:35:00',
        'game_name': 'Just Chatting'
    })

    print(stream_data['id'])

    # answer = asyncio.run(ai_bot.rate_title('Mister Streamer'))
    answer = asyncio.run(ai_bot.advert_title(Stream(None, data=stream_data)))

    # print(answer)
