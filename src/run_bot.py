from src.bots.bots_crud import get_bot_by_name, update_session_data
from src.database.db import async_session
from src.ai_services.ai_generate_reply import generate_reply
from src.twitter.tweets import find_most_viral_tweet
from src.twitter.twitter_portal import TwitterPortal
from src.twitter.tweets_crud import tweet_exists, create_tweet, update_tweet_reply
import logging
import asyncio

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def run_bot(bot_name: str, max_tweets: int = 8) -> None:
    """
    Main function to run the bot.

    Parameters
    ----------
    bot_name : str
    """
    logger.info(f"Running bot {bot_name} with {max_tweets} tweets")

    async with async_session() as session:
        bot_data = await get_bot_by_name(session, bot_name)
        if not bot_data:
            raise ValueError(f"Bot {bot_name} not found")

        logger.info(f"Bot {bot_name} found")
        twitter_portal = TwitterPortal(
            headless=True, session=bot_data.session_data, logger=logger
        )
        async with twitter_portal:
            await twitter_portal.get_following_tweets_page(
                username=bot_data.username,
                password=bot_data.password_decrypted.get_secret_value(),
            )
            session_data = await twitter_portal.get_session()
            await update_session_data(session, bot_data.id, session_data)
            tweets = await twitter_portal.scrape_home_timeline(max_tweets)
            logging.info(f"Tweets: {len(tweets)}")

            most_viral = find_most_viral_tweet(tweets)

            if most_viral:
                logging.info(
                    f"Most viral tweet: {most_viral.author} - {most_viral.text[:100]}... "
                    f"Viral score: {most_viral.viral_score}"
                )
                if await tweet_exists(session, most_viral.author, most_viral.text):
                    logging.info("Tweet already exists in database")
                    return

                logger.info("Creating tweet in database")
                db_tweet = await create_tweet(session, bot_data.id, most_viral)

                logger.info("Generating reply")
                reply_text = await generate_reply(most_viral)

                logger.info("Applying bot actions")
                await twitter_portal.apply_bot_actions(
                    tweet=most_viral, reply_text=reply_text
                )
                await update_tweet_reply(session, db_tweet.id, reply_text)
            else:
                logger.info("No most viral tweet found")

            logger.info("Bot finished")


if __name__ == "__main__":
    asyncio.run(run_bot("bebbogdan"))
