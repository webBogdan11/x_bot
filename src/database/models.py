from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.db import Base, TableNameMixin, TimestampMixin, int_pk


class Bots(TableNameMixin, TimestampMixin, Base):
    id: Mapped[int_pk]
    bot_name: Mapped[str | None] = mapped_column(unique=True)
    username: Mapped[str | None]
    password: Mapped[str | None]
    login: Mapped[str | None]
    session: Mapped[dict | None]

    tweets: Mapped[list["Tweets"]] = relationship(
        "Tweets", back_populates="bot", cascade="all, delete-orphan"
    )


class Tweets(TableNameMixin, TimestampMixin, Base):
    id: Mapped[int_pk]
    bot_id: Mapped[int] = mapped_column(ForeignKey("bots.id"))
    reply_message: Mapped[str | None]
    tweet_content: Mapped[str]
    tweet_author: Mapped[str]
    likes: Mapped[int] = mapped_column(default=0)
    retweets: Mapped[int] = mapped_column(default=0)
    views: Mapped[int] = mapped_column(default=0)
    url: Mapped[str]
    viral_score: Mapped[float] = mapped_column(default=0.0)
    hash: Mapped[str]

    bot: Mapped["Bots"] = relationship("Bots", back_populates="tweets")
