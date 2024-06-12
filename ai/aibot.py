"""AI Bot"""
import asyncio

from openai import AsyncOpenAI


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


if __name__ == '__main__':
    # test bot
    from dotenv import load_dotenv

    load_dotenv()

    ai_bot = AIBot(client=AsyncOpenAI())
    answer = asyncio.run(ai_bot.rate_title('Mister Streamer'))

    print(answer)
