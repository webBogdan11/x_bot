from pydantic import BaseModel
from typing import Iterable
import re


class Tweet(BaseModel):
    author: str
    text: str
    likes: int
    retweets: int
    replies: int
    views: int
    url: str

    @property
    def viral_score(self) -> int:
        """
        Heuristic virality score.

        Retweets amplify reach far more than likes, so give them 2× weight.
        Adjust the weights if you want a different balance.
        """
        return self.likes + 2 * self.retweets


def find_most_viral_tweet(tweets: Iterable[Tweet]) -> Tweet | None:
    """
    Return the tweet with the highest `.viral_score`.
    If *tweets* is empty, return ``None`` instead of raising.

    Parameters
    ----------
    tweets : Iterable[Tweet]
    Returns
    -------
    Tweet | None
    """
    return max(tweets, key=lambda t: t.viral_score, default=None)


def parse_twitter_count(raw: str) -> int:
    """
    Parse a Twitter count string into an integer.

    Parameters
    ----------
    raw : str
    Returns
    -------
    """
    raw = raw.replace(",", "").strip()
    if not raw:
        return 0
    m = re.match(r"([\d.]+)([KMB]?)", raw, re.I)
    if not m:
        return 0
    number, suffix = m.groups()
    number = float(number)
    mult = {"": 1, "K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
    return int(number * mult.get(suffix.upper(), 1))
