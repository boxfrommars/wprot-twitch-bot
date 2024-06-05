"""
Title related stuff
"""


from datetime import datetime, UTC
from sqlite3 import Row

from aiosqlite import Connection
from dateutil import parser
from twitchio import Chatter  # type: ignore


class TitleManager:
    """Handle titles"""
    def __init__(
            self,
            db: Connection,
            cooldown: int = 6 * 60 * 60,  # 6 hours
            lifetime: int = 7 * 24 * 60 * 60) -> None:  # a week

        self.db = db
        # if user doesn't posted `cooldown` seconds then title needed
        self.cooldown = cooldown
        # title purchased for `lifetime` seconds
        self.lifetime = lifetime

    async def set_title(self, title: str, user: Chatter) -> None:
        """Add or update user title"""
        cur = await self.db.cursor()
        await cur.execute(  # upsert title
            """
            INSERT INTO titles (
                user_id, username,
                purchased_at, last_posted_at,
                title)
            VALUES (
                :user_id, :username,
                :purchased_at, :purchased_at,
                :title)
            ON CONFLICT (user_id)
            DO UPDATE SET
                username=:username,
                purchased_at=:purchased_at, last_posted_at=:purchased_at,
                title=:title
            """,
            {
                'user_id': user.id,
                'username': user.name,
                'purchased_at': datetime.now(UTC).isoformat(),
                'title': title
            }
        )
        await self.db.commit()

    async def get_title(self, user: Chatter) -> Row | None:
        """Checks if message is the first for a long time"""
        cur = await self.db.cursor()
        await cur.execute(
            'SELECT * FROM titles WHERE user_id = :user_id',
            {'user_id': user.id}
        )

        return await cur.fetchone()

    def is_greeting_needed(self, title_record: Row) -> bool:
        """
        Check is greeting needed (subscription is active
        and more than cooldown seconds from last message)
        """
        purchased_at = parser.parse(title_record['purchased_at'])
        last_posted_at = parser.parse(title_record['last_posted_at'])
        current_dt = datetime.now(UTC)

        is_greeting_needed = (
            ((current_dt - purchased_at).total_seconds() < self.lifetime)
            and ((current_dt - last_posted_at).total_seconds() > self.cooldown)
        )

        return is_greeting_needed

    async def update_last_posted_at(self, user: Chatter) -> None:
        """Update last message time"""
        cur = await self.db.cursor()
        await cur.execute(
            'UPDATE titles SET last_posted_at = :now WHERE user_id = :user_id',
            {
                'now': datetime.now(UTC).isoformat(),
                'user_id': user.id
            }
        )
        await self.db.commit()

    async def up(self) -> None:
        """Create tables if not exists"""
        cur = await self.db.cursor()
        await cur.execute(
            """
            CREATE TABLE IF NOT EXISTS titles (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                purchased_at DATETIME,
                last_posted_at DATETIME,
                title TEXT
            )
            """
        )
        await self.db.commit()
