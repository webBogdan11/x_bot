from playwright.async_api import (
    async_playwright,
    TimeoutError,
    ElementHandle,
)
from logging import Logger
import random

from src.twitter.tweets import Tweet, parse_twitter_count
from src.utils.portal_utils import human_type, async_retry


SELECTOR_CONFIG = {
    "AUTHOR_SELECTOR": 'div[data-testid="User-Name"] span',
    "TEXT_SELECTOR": 'div[data-testid="tweetText"] span, div[data-testid="tweetText"]',
    "URL_SELECTOR": 'a[href*="/status/"]',
    "LIKE_SELECTOR": 'button[data-testid="like"]    div[dir="ltr"] span span span',
    "RETWEET_SELECTOR": 'button[data-testid="retweet"] div[dir="ltr"] span span span',
    "REPLY_SELECTOR": 'button[data-testid="reply"]   div[dir="ltr"] span span span',
    "VIEW_SELECTOR": 'a[href*="/analytics"]      div[dir="ltr"] span span span',
    "TWEET_SELECTOR": 'div[aria-label="Home timeline"] article',
    "DETAIL_TWEET_SELECTOR": "article[data-testid='tweet']",
    "DETAIL_TWEET_LIKE_SELECTOR": 'button[data-testid="like"]',
    "DETAIL_TWEET_UNLIKE_SELECTOR": 'button[data-testid="unlike"]',
    "DETAIL_TWEET_REPLY_SELECTOR": 'button[data-testid="reply"]',
    "DETAIL_TWEET_REPLY_TEXTBOX_SELECTOR": 'div[role="dialog"] div[role="textbox"]',
    "DETAIL_TWEET_REPLY_BUTTON_SELECTOR": 'button[data-testid="tweetButton"]',
    "DETAIL_TWEET_RETWEET_SELECTOR": 'button[data-testid="retweet"]',
}


class BaseService:
    def __init__(
        self,
        logger: Logger,
        headless: bool = True,
        session: dict | None = None,
    ):
        self.logger = logger
        self.headless = headless

        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.use_external_context = False
        self.session = session

    def set_context(self, context):
        """Dynamically set the browser instance."""
        self.context = context
        self.use_external_context = True

    async def get_session(self) -> dict:
        return await self.context.storage_state()

    async def __aenter__(self):
        """
        Asynchronous context manager entry. Starts Playwright and opens a browser.
        :return: The instance of the BaseService.
        """
        if not getattr(self, "use_external_context", False):
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=["--disable-pdf-viewer", "--disable-print-preview"],
            )
            self.context = await self.browser.new_context(
                ignore_https_errors=True,
                accept_downloads=True,
                storage_state=self.session,
            )

        self.page = await self.context.new_page()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Asynchronous context manager exit. Closes the browser and stops Playwright.

        :param exc_type: Exception type.
        :param exc_val: Exception value.
        :param exc_tb: Traceback of the exception.
        """
        if hasattr(self, "page"):
            await self.page.close()
        if not getattr(self, "use_external_context", False):
            await self.browser.close()
            await self.playwright.stop()


class TwitterPortal(BaseService):
    def __init__(
        self, logger: Logger, headless: bool = True, session: dict | None = None
    ):
        super().__init__(logger, headless, session)

    async def login(self, username: str, password: str) -> None:
        """
        Login to Twitter.

        Parameters
        ----------
        username : str
        password : str
        """
        await self.page.wait_for_selector('input[name="text"]', timeout=10_000)
        await human_type(self.page, 'input[name="text"]', username)
        await self.page.wait_for_timeout(2_000)
        await self.page.eval_on_selector('input[name="text"]', "el => el.blur()")
        await self.page.click("h1#modal-header")
        await self.page.click('span:has-text("Next")')

        await self.page.wait_for_selector('input[name="password"]', timeout=10_000)
        await human_type(self.page, 'input[name="password"]', password)
        await self.page.wait_for_timeout(2_000)
        await self.page.click('span:has-text("Log in")')
        await self.page.wait_for_selector(
            'div[aria-label="Home timeline"]', timeout=50_000
        )

    @async_retry(retries=3)
    async def get_following_tweets_page(self, username: str, password: str) -> None:
        """
        Get the following tweets page.

        Parameters
        ----------
        username : str
        password : str
        """
        self.logger.info("Getting following tweets page")
        await self.page.goto("https://x.com/home", timeout=50_000)
        try:  # ≤7 s: already logged in?
            await self.page.wait_for_selector(
                'div[aria-label="Home timeline"]', timeout=7_000
            )
            self.logger.info("Already logged in")
        except TimeoutError:
            self.logger.info("Not logged in")
            await self.login(username, password)

        await self.page.get_by_role("tab", name="Following").click()
        self.logger.info("Waiting for following tweets page")
        await self.page.wait_for_timeout(2_000)

    async def _extract_tweet(self, article: ElementHandle) -> Tweet | None:
        """
        Extract tweet information from a tweet article.

        Parameters
        ----------
        article : ElementHandle
        Returns
        -------
        """
        author_el = await article.query_selector(SELECTOR_CONFIG["AUTHOR_SELECTOR"])
        text_nodes = await article.query_selector_all(SELECTOR_CONFIG["TEXT_SELECTOR"])
        url = await article.query_selector(SELECTOR_CONFIG["URL_SELECTOR"])

        if not author_el or not text_nodes or not url:
            return None

        author = (await author_el.inner_text()).strip()
        text = " ".join([(await n.inner_text()).strip() for n in text_nodes]).strip()
        url = await url.get_attribute("href")

        likes = (
            parse_twitter_count(
                await (
                    await article.query_selector(SELECTOR_CONFIG["LIKE_SELECTOR"])
                ).inner_text()
            )
            if await article.query_selector(SELECTOR_CONFIG["LIKE_SELECTOR"])
            else 0
        )
        retw = (
            parse_twitter_count(
                await (
                    await article.query_selector(SELECTOR_CONFIG["RETWEET_SELECTOR"])
                ).inner_text()
            )
            if await article.query_selector(SELECTOR_CONFIG["RETWEET_SELECTOR"])
            else 0
        )
        repl = (
            parse_twitter_count(
                await (
                    await article.query_selector(SELECTOR_CONFIG["REPLY_SELECTOR"])
                ).inner_text()
            )
            if await article.query_selector(SELECTOR_CONFIG["REPLY_SELECTOR"])
            else 0
        )
        views = (
            parse_twitter_count(
                await (
                    await article.query_selector(SELECTOR_CONFIG["VIEW_SELECTOR"])
                ).inner_text()
            )
            if await article.query_selector(SELECTOR_CONFIG["VIEW_SELECTOR"])
            else 0
        )

        return Tweet(
            author=author,
            text=text,
            likes=likes,
            retweets=retw,
            replies=repl,
            views=views,
            url=url,
        )

    @async_retry(retries=3)
    async def scrape_home_timeline(self, max_tweets: int = 20) -> list[Tweet]:
        """
        Scrape the home timeline.

        Parameters
        ----------
        max_tweets : int
        Returns
        -------
        """
        await self.page.wait_for_selector(
            'div[aria-label="Home timeline"]', timeout=15_000
        )
        self.logger.info("Timeline loaded")

        tweets: list[Tweet] = []
        seen: set[str] = set()

        while len(tweets) < max_tweets:
            cards = await self.page.query_selector_all(
                SELECTOR_CONFIG["TWEET_SELECTOR"]
            )
            for art in cards:
                if len(tweets) >= max_tweets:
                    break

                box = await art.bounding_box()
                if box:
                    # pick a random point inside the tweet
                    target_x = box["x"] + random.uniform(0, box["width"])
                    target_y = box["y"] + random.uniform(0, box["height"])
                    # move in a few small steps
                    await self.page.mouse.move(
                        target_x, target_y, steps=random.randint(5, 15)
                    )

                self.logger.info(f"Scraping tweet... {len(tweets)}/{max_tweets}")
                t = await self._extract_tweet(art)
                if not t:
                    continue

                self.logger.info(f"Tweet: {t.author}: {t.text[:30]}… {t.url}")
                if t.text not in seen:
                    self.logger.info(f"Adding tweet: {t.url}")
                    tweets.append(t)
                    seen.add(t.url)
                else:
                    self.logger.info(f"Tweet already seen: {t.url}")

                await self.page.wait_for_timeout(random.uniform(300, 1200))

            if len(tweets) >= max_tweets:
                break

            scroll_dist = random.uniform(1500, 2500)
            await self.page.mouse.wheel(0, scroll_dist)

            await self.page.wait_for_timeout(random.uniform(1500, 3000))

        return tweets[:max_tweets]

    @async_retry(retries=3)
    async def click_like(self) -> bool:
        """
        Likes *tweet* if it is not already liked.
        Returns True ⇢ a click happened, False ⇢ already liked / button missing.
        """
        article = self.page.locator(
            SELECTOR_CONFIG["DETAIL_TWEET_SELECTOR"]
        ).first.get_by_role("group")

        await self.page.wait_for_timeout(random.uniform(1500, 3000))

        unlike_btn = article.locator(SELECTOR_CONFIG["DETAIL_TWEET_UNLIKE_SELECTOR"])
        count_unlike = await unlike_btn.count()
        self.logger.info(f"Count of unlike buttons: {count_unlike}")
        if count_unlike > 0:
            self.logger.info("Tweet already liked (button shows 'unlike')")
            return False

        like_btn = article.locator(SELECTOR_CONFIG["DETAIL_TWEET_LIKE_SELECTOR"])
        await like_btn.click()
        await self.page.wait_for_timeout(random.uniform(400, 900))
        self.logger.info("Tweet liked ✔")
        return True

    @async_retry(retries=3)
    async def reply_to_tweet(self, text: str) -> None:
        """
        Opens the reply composer for *tweet*, types *text* (human-ish),
        and presses “Post”.

        Parameters
        ----------
        text : str
        """
        await self.page.locator(
            SELECTOR_CONFIG["DETAIL_TWEET_REPLY_SELECTOR"]
        ).first.click()

        # Composer is a modal dialog – wait for it and find the textbox
        dialog = self.page.get_by_role("group").get_by_role("dialog")
        await dialog.wait_for(state="visible", timeout=10_000)

        await human_type(
            self.page, SELECTOR_CONFIG["DETAIL_TWEET_REPLY_TEXTBOX_SELECTOR"], text
        )
        await self.page.wait_for_timeout(random.uniform(300, 700))

        # The ‘Tweet’ / ‘Reply’ button inside the dialog
        await dialog.locator(
            SELECTOR_CONFIG["DETAIL_TWEET_REPLY_BUTTON_SELECTOR"]
        ).click()
        self.logger.info("Reply posted ✔")
        await self.page.wait_for_timeout(random.uniform(800, 1500))

    @async_retry(retries=3)
    async def click_retweet(self) -> bool:
        """
        Retweets *tweet* if it is not already retweeted.
        Returns True ⇢ a click happened, False ⇢ already retweeted / button missing.
        """
        btn = self.page.locator(SELECTOR_CONFIG["DETAIL_TWEET_RETWEET_SELECTOR"]).first
        await btn.click()
        await self.page.wait_for_timeout(random.uniform(400, 900))  # tiny human pause

        confirm_btn = self.page.get_by_text("Repost")
        await confirm_btn.click()
        await self.page.wait_for_timeout(random.uniform(400, 900))  # tiny human pause

        self.logger.info("Tweet retweeted ✔")
        return True

    async def apply_bot_actions(self, tweet: Tweet, reply_text: str) -> None:
        """
        Apply bot actions to a tweet.

        Parameters
        ----------
        tweet : Tweet
        reply_text : str
        """
        await self.page.goto(f"https://x.com{tweet.url}", timeout=50_000)
        if await self.click_like():
            await self.reply_to_tweet(reply_text)
            await self.click_retweet()
        else:
            self.logger.info("Tweet already liked (button shows 'unlike')")

        self.logger.info("Bot actions applied")
