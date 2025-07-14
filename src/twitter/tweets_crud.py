import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database.models import Tweets
from src.twitter.tweets import Tweet as TweetModel


def _compute_tweet_hash(author: str, text: str) -> str:
    hash_input = (author + text).encode("utf-8")
    return hashlib.sha256(hash_input).hexdigest()


async def create_tweet(
    session: AsyncSession,
    bot_id: int,
    tweet: TweetModel,
) -> Tweets:
    """
    Create a new tweet record in the database.

    Computes a SHA-256 hash of author+text to uniquely identify duplicates,
    calculates the viral score, and inserts the record.

    Parameters
    ----------
    session : AsyncSession
    bot_id : int
    tweet : TweetModel
    Returns
    """
    # Compute unique hash
    tweet_hash = _compute_tweet_hash(tweet.author, tweet.text)

    db_tweet = Tweets(
        bot_id=bot_id,
        tweet_author=tweet.author,
        tweet_content=tweet.text,
        likes=tweet.likes,
        retweets=tweet.retweets,
        views=tweet.views,
        url=tweet.url,
        viral_score=tweet.viral_score,
        hash=tweet_hash,
    )
    session.add(db_tweet)
    await session.commit()
    await session.refresh(db_tweet)
    return db_tweet


async def tweet_exists(
    session: AsyncSession,
    author: str,
    content: str,
) -> bool:
    """
    Check if a tweet with the given author and content already exists.

    Generates the same SHA-256 hash of author+content and queries the DB.

    Parameters
    ----------
    session : AsyncSession
    author : str
    content : str
    Returns
    -------
    """
    tweet_hash = _compute_tweet_hash(author, content)
    result = await session.execute(select(Tweets).where(Tweets.hash == tweet_hash))
    return result.scalars().first() is not None


async def update_tweet_reply(
    session: AsyncSession,
    tweet_id: int,
    ai_reply: str,
) -> Tweets | None:
    """
    Update the reply_message of a tweet by its ID to add an AI-generated reply.

    Returns the updated Tweets object, or None if not found.

    Parameters
    ----------
    session : AsyncSession
    tweet_id : int
    ai_reply : str
    Returns
    -------
    """
    tweet = await session.get(Tweets, tweet_id)
    if not tweet:
        return None
    tweet.reply_message = ai_reply
    await session.commit()
    await session.refresh(tweet)
    return tweet
