"""AI Bot"""
import asyncio

from openai import AsyncOpenAI
from ai.prompts import prompts


class AIBot:
    """AI Bot"""
    def __init__(self, client: AsyncOpenAI) -> None:

        self.client = client

    async def rate_title(self, title: str):
        """Rate title"""
        return await self.completion(
            prompt=prompts['rate_title_as_critic'],
            query=title)

    async def completion(self, prompt: str, query: str) -> str | None:
        """Get completion"""
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
            return completion.choices[0].message.content

        return None


async def main(title):
    """Test AIBot"""
    ai_bot = AIBot(AsyncOpenAI())
    answer = await ai_bot.rate_title(title)
    print(answer)


if __name__ == '__main__':
    from dotenv import load_dotenv

    load_dotenv()

    asyncio.run(main('мой скромный создатель'))
