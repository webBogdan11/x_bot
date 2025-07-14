# Twitter Bot Automation

## Introduction

This project provides an automated Twitter interaction system powered by configurable “bots.” It uses a PostgreSQL database to manage bot credentials and store tweets. Passwords are securely hashed before storage. Once a bot is registered via the provided creation script, you can run the bot by its predefined name. The bot will:

1. Scrape a specified number of tweets from Twitter.
2. Identify the most viral tweets based on engagement metrics.
3. Perform actions such as liking, retweeting, and replying.
4. Store raw and processed tweet data in the database.
5. Generate AI-driven responses by calling the OpenAI API via LangChain, with observability provided by LangSmith (tracking tokens, costs, and logs).

All components run inside Docker containers, including a headless browser for scraping and a PostgreSQL instance for data storage.
