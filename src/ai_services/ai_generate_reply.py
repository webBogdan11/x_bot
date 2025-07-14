from src.twitter.tweets import Tweet
from langchain_openai import ChatOpenAI
from langsmith import traceable


@traceable(run_name="generate_reply")
async def generate_reply(tweet: Tweet) -> str:
    """
    Very simple LLM-powered reply; tweak the prompt to your taste.

    Parameters
    ----------
    tweet : Tweet
    Returns
    -------
    str
    """
    llm = ChatOpenAI(model="gpt-4.1-mini")

    prompt = (
        "Напиши коротку, дружню відповідь українською на цей твіт:\n\n"
        f"«{tweet.text}»\n\n"
        "Будь позитивним та підтримуючим."
        "Твіт повинен бути коротким і лаконічним. Десь пару речень."
    )
    llm_response = await llm.ainvoke(prompt)
    return llm_response.content
