# src/bots.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from cryptography.fernet import Fernet, InvalidToken
from pydantic import BaseModel, SecretStr

from src.database.models import Bots
from src.settings import settings

_fernet = Fernet(settings.fernet_key.encode())


class Bot(BaseModel):
    bot_name: str
    username: str
    password_decrypted: SecretStr
    login: str
    session_data: dict
    id: int


async def create_bot(
    session: AsyncSession,
    bot_name: str,
    username: str,
    password: str,
    login: str,
    session_data: dict | None = None,
) -> Bots:
    """
    Create a new bot in the database.

    Parameters
    ----------
    session : AsyncSession
    bot_name : str
    username : str
    password : str
    """
    encrypted = _fernet.encrypt(password.encode()).decode()

    bot = Bots(
        bot_name=bot_name,
        username=username,
        password=encrypted,
        login=login,
        session=session_data or {},
    )
    session.add(bot)
    await session.commit()
    await session.refresh(bot)
    return bot


async def get_bot_by_name(
    session: AsyncSession,
    bot_name: str,
) -> Bot | None:
    """
    Retrieve a bot by name and decrypt its password before returning.

    Parameters
    ----------
    session : AsyncSession
    bot_name : str
    -------
    Bot | None
    """
    result = await session.execute(select(Bots).where(Bots.bot_name == bot_name))
    bot = result.scalar_one_or_none()
    if not bot or not bot.password:
        return bot

    try:
        decrypted = _fernet.decrypt(bot.password.encode()).decode()
        return Bot(
            bot_name=bot.bot_name,
            username=bot.username,
            password_decrypted=SecretStr(decrypted),
            login=bot.login,
            session_data=bot.session,
            id=bot.id,
        )
    except InvalidToken:
        raise ValueError("Invalid token for bot. Please check the fernet key.")


async def update_session_data(
    session: AsyncSession,
    bot_id: int,
    session_data: dict,
) -> Bots | None:
    """
    Update only the session data for a bot.

    Parameters
    ----------
    session : AsyncSession
    bot_id : int
    session_data : dict
    -------
    """
    bot = await session.get(Bots, bot_id)
    if not bot:
        return None

    bot.session = session_data
    await session.commit()
    await session.refresh(bot)
    return bot
