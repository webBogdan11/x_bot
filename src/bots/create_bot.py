import argparse
import asyncio
import getpass

from src.database.db import async_session
from src.bots.bots_crud import create_bot as _create_bot


async def _async_create_bot(
    bot_name: str,
    username: str,
    password: str,
    login: str,
) -> None:
    """
    Create a new bot in the database.

    Parameters
    ----------
    bot_name : str
    username : str
    password : str
    login : str
    Returns
    -------
    """

    async with async_session() as session:
        bot = await _create_bot(
            session=session,
            bot_name=bot_name,
            username=username,
            password=password,
            login=login,
        )
        print(
            f"✅ Created bot:\n  id={bot.id}\n  name={bot.bot_name}\n  username={bot.username}"
        )


def main() -> None:
    """
    Main function to create a new bot in the database.

    Parameters
    ----------
    bot_name : str
    username : str
    password : str
    login : str
    """
    parser = argparse.ArgumentParser(
        prog="create-bot", description="Create a new bot in the database."
    )
    parser.add_argument(
        "--bot-name",
        "-n",
        required=True,
        help="Unique name for your bot (e.g. 'my_twitter_helper')",
    )
    parser.add_argument(
        "--username", "-u", required=True, help="The bot's login username"
    )
    parser.add_argument(
        "--login",
        "-l",
        required=True,
        help="Login endpoint or identifier (e.g. 'twitter.com')",
    )
    parser.add_argument(
        "--password", "-p", help="Password (if omitted, you'll be prompted securely)"
    )
    args = parser.parse_args()

    if args.password:
        password = args.password
    else:
        password = getpass.getpass("Password: ")

    asyncio.run(
        _async_create_bot(
            bot_name=args.bot_name,
            username=args.username,
            password=password,
            login=args.login,
        )
    )


if __name__ == "__main__":
    main()
