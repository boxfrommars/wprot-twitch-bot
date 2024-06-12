"""
Title related stuff
"""


from datetime import datetime, UTC
from sqlite3 import Row

from aiosqlite import Connection
import aiosqlite
from dateutil import parser
from twitchio import PartialChatter  # type: ignore


class TitleManager:
    """Handle titles"""
    def __init__(
            self,
            db_name: str,
            template: str = '{title} @{username} вошёл в чат',
            cooldown: int = 6 * 60 * 60,  # 8 hours
            lifetime: int = 14 * 24 * 60 * 60) -> None:  # a week

        self.db_name = db_name
        self.db: Connection | None
        # if user doesn't posted `cooldown` seconds then title needed
        self.cooldown = cooldown
        # title purchased for `lifetime` seconds
        self.lifetime = lifetime
        self.template = template

    async def set_title(self, title: str, user: PartialChatter) -> None:
        """Add or update user title"""
        if not self.db:
            raise RuntimeError('No DB connection')

        cur = await self.db.cursor()
        await cur.execute(  # upsert title
            """
            INSERT INTO titles (
                username,
                purchased_at,
                last_posted_at,
                title)
            VALUES (
                :username,
                :purchased_at,
                :purchased_at,
                :title)
            ON CONFLICT (username)
            DO UPDATE SET
                username=:username,
                purchased_at=:purchased_at,
                last_posted_at=:purchased_at,
                title=:title
            """,
            {
                'username': user.name,
                'purchased_at': datetime.now(UTC).isoformat(),
                'title': title
            }
        )
        await self.db.commit()

    async def get_title(self, user: PartialChatter) -> Row | None:
        """Get user title"""
        if not self.db:
            raise RuntimeError('No DB connection')

        cur = await self.db.cursor()
        await cur.execute(
            'SELECT * FROM titles WHERE username = :username',
            {'username': user.name}
        )

        return await cur.fetchone()

    async def delete_title(self, user: PartialChatter) -> None:
        """Delete user title"""
        if not self.db:
            raise RuntimeError('No DB connection')

        cur = await self.db.cursor()
        await cur.execute(
            'DELETE FROM titles WHERE username = :username',
            {'username': user.name}
        )

        await self.db.commit()

    async def update_last_posted_at(self, user: PartialChatter) -> None:
        """Update last message time"""
        if not self.db:
            raise RuntimeError('No DB connection')

        cur = await self.db.cursor()
        await cur.execute(
            """
            UPDATE titles
            SET last_posted_at = :now
            WHERE username = :username
            """,
            {
                'now': datetime.now(UTC).isoformat(),
                'username': user.name
            }
        )
        await self.db.commit()

    def greeting(self, title_record: Row) -> str:
        """Create greeting from title"""
        return self.template.format(**title_record)

    def is_active(self, title_record: Row) -> bool:
        """Check subsctipion is active"""
        purchased_at = parser.parse(title_record['purchased_at'])
        current_dt = datetime.now(UTC)

        is_active = (current_dt - purchased_at).total_seconds() < self.lifetime

        return is_active

    def is_greeting_needed(self, title_record: Row) -> bool:
        """
        Check is greeting needed (subscription is active
        and more than cooldown seconds from last message)
        """
        last_posted_at = parser.parse(title_record['last_posted_at'])
        current_dt = datetime.now(UTC)

        is_greeting_needed = (
            self.is_active(title_record)
            and ((current_dt - last_posted_at).total_seconds() > self.cooldown)
        )

        return is_greeting_needed

    def format_title_info(self, title_record: Row) -> str:
        """Get summary text about title"""
        purchased_at = parser.parse(title_record["purchased_at"])

        is_active = self.is_active(title_record)

        return (
            f'@{title_record["username"]}, '
            f'Your title: "{title_record["title"]}" '
            f'purchased on {purchased_at.strftime('%Y-%m-%d')} '
            f'({"Active" if is_active else "Deactivated"})'
        )

    async def up(self) -> None:
        """Create tables if not exists"""
        self.db = await aiosqlite.connect(self.db_name)
        self.db.row_factory = Row  # get data from sqlite as Mappable obj

        cur = await self.db.cursor()
        await cur.execute(
            """
            CREATE TABLE IF NOT EXISTS titles (
                username TEXT PRIMARY KEY,
                purchased_at DATETIME,
                last_posted_at DATETIME,
                title TEXT
            )
            """
        )
        await self.db.commit()

    async def close(self) -> None:
        """Close connection"""
        if self.db:
            await self.db.close()
