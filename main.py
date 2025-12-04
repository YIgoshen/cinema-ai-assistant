from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from pathlib import Path
import csv
import os
import requests

# FastAPI App
app = FastAPI(root_path="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage
data: List[Dict[str, Any]] = []  # Храним сообщения + reasoning

# CSV Loading
MOVIES_DB: Dict[str, Dict] = {}


def load_local_movies() -> None:
    csv_path = Path("data/movies.csv")
    if not csv_path.exists():
        print(f"CSV NOT FOUND: {csv_path.resolve()}")
        return

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            loaded = 0
            for row in reader:
                title = row.get("Series_Title", "").strip()
                if title:
                    MOVIES_DB[title.lower()] = row
                    loaded += 1
            print(f"Successully loaded {loaded} movies from movies.csv")
    except Exception as e:
        print(f"Error loading CSV: {e}")


load_local_movies()


# LangChain Setup
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationSummaryBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.tools import tool

load_dotenv()

OMDB_URI = f"http://www.omdbapi.com/?apikey={os.getenv('OMDB_API_KEY')}"

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY"),
)

memory = ConversationSummaryBufferMemory(
    llm=llm,
    max_token_limit=400,
    memory_key="history",
    return_messages=True,
)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            Ты — CinemaBot, дружелюбный и увлечённый эксперт по кино. 
            Ты всегда отвечаешь на русском языке, с энтузиазмом, используешь эмодзи.

            ### Доступные инструменты:
            У тебя есть 3 инструмента. Используй их ТОЛЬКО когда запрос пользователя явно соответствует их назначению:

            1. search_movie — когда пользователь спрашивает про конкретный фильм:
            • «Расскажи про Титаник», «Что за фильм Матрица?», «Кто режиссёр Интpip freeze > requirements.txt
ерстеллара?», «Какой рейтинг у Начала?» → используй search_movie

            2. compare_two_movies — когда пользователь сравнивает два фильма:
            • «Интерстеллар или Начало?», «Что лучше: Дюна или Оппенгеймер?», «Сравни Бойцовский клуб и Матрицу» → используй compare_two_movies

            3. get_movies_by_genre — когда пользователь хочет рекомендации по жанру:
            • «Посоветуй комедию», «Лучшие боевики», «Что посмотреть из фантастики», «Топ-5 драм», «Хороший триллер» → используй get_movies_by_genre

            Если запрос не попадает под эти случаи — отвечай сам, без инструментов.

            ### Работа с памятью:
            Ты помнишь весь предыдущий диалог. Ссылайся на него, если пользователь упоминает прошлые фильмы или предпочтения.
            Пример: пользователь сказал «Люблю Нолана» → потом «Что ещё посмотреть?» → предложи другой фильм Нолана.

            ### Примеры (few-shot):

            Пользователь: Привет!
            Ты: Привет! Я CinemaBot — твой личный гид по миру кино. Спрашивай что угодно: фильмы, жанры, сравнения — я всё знаю! 

            Пользователь: Расскажи про фильм "Оппенгеймер"
            Ты: (вызываешь search_movie) → Оппенгеймер (2023) — биографическая драма от Кристофера Нолана... 

            Пользователь: А что лучше — Оппенгеймер или Дюна?
            Ты: (вызываешь compare_two_movies) → Давай сравним! Оппенгеймер: 8.6/10... Дюна: 8.3/10... Победитель — Оппенгеймер! 

            Пользователь: Посоветуй комедию
            Ты: (вызываешь get_movies_by_genre) → Вот топ комедий из тысячи лучших: 1. The Intouchables... 

            Пользователь: Спасибо! А что-то лёгкое на вечер?
            Ты: (без инструмента, с памятью) Конечно! Ты любишь комедии — попробуй «1+1» (The Intouchables) или «Похмельные игры» — лёгкие и очень смешные! 

            Всегда будь позитивным, используй эмодзи!
            """,
        ),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)


# Tools
@tool
def search_movie(query: str) -> Dict[str, Any]:
    """Используй, когда пользователь:
    • спрашивает про конкретный фильм по названию
    • хочет узнать информацию о фильме (год, режиссёр, рейтинг, актёры, сюжет и т.д.)
    • говорит «что за фильм», «расскажи про», «покажи», «найди фильм», «информация о фильме», «кто снимался в», «кто режиссёр», «какой рейтинг у» и т.п.
    Название фильма нужно искать на английском языке (например, «Титаник» → «Titanic»).
    """

    q = query.strip().lower()

    # Локальная база
    for movie in MOVIES_DB.values():
        if q in movie["Series_Title"].lower():
            return {
                "title": movie["Series_Title"],
                "year": movie["Released_Year"],
                "director": movie["Director"],
                "genre": movie["Genre"],
                "rating": movie["IMDB_Rating"],
                "stars": [
                    movie.get(f"Star{i}") for i in range(1, 5) if movie.get(f"Star{i}")
                ],
                "overview": movie["Overview"],
                "source": "local",
            }

    # OMDB fallback
    try:
        resp = requests.get(f"{OMDB_URI}&t={query.strip()}").json()
        if resp.get("Response") == "True":
            return {
                "title": resp["Title"],
                "year": resp["Year"],
                "director": resp["Director"],
                "genre": resp["Genre"],
                "rating": resp.get("imdbRating", "N/A"),
                "stars": [a.strip() for a in resp["Actors"].split(",")[:4]],
                "overview": resp["Plot"],
                "source": "OMDB",
            }
    except:
        pass

    return {"error": "Movie not found"}


@tool
def compare_two_movies(movie1: str, movie2: str) -> str:
    """Используй, когда пользователь:
    • просит сравнить два фильма
    • спрашивает «что лучше», «какой круче», «сравни», «можешь сравнить», «versus», «против», «чем отличается», «какой выше рейтинг», «кто выиграет» и т.п.
    • явно упоминает два названия фильмов в одном запросе с намёком на сравнение
    Примеры: «Интерстеллар или Начало?», «что лучше: Матрица или Бойцовский клуб?», «сравни Оппенгеймер и Дюну».
    """

    m1 = search_movie.invoke({"query": movie1})
    m2 = search_movie.invoke({"query": movie2})

    if "error" in m1 or "error" in m2:
        return f"Не удалось найти один из фильмов: {' или '.join([movie1, movie2])}"

    winner = (
        m1["title"]
        if float(m1.get("rating", 0)) > float(m2.get("rating", 0))
        else m2["title"]
    )

    return f"""
    СРАВНЕНИЕ ФИЛЬМОВ

    1. {m1['title']} ({m1['year']})
    → IMDb: {m1['rating']} | Режиссёр: {m1['director']}

    2. {m2['title']} ({m2['year']})
    → IMDb: {m2['rating']} | Режиссёр: {m2['director']}

    Победитель по рейтингу: {winner}
    """.strip()


@tool
def get_movies_by_genre(genre: str) -> str:
    """Используй, когда пользователь:
    • просит посоветовать или порекомендовать фильмы определённого жанра
    • спрашивает «лучшие комедии», «топ боевиков», «что посмотреть из фантастики», «хорошие драмы», «фильмы ужасов», «посоветуй триллер», «дай комедию» и т.п.
    • говорит «хочу что-то из [жанр]», «ищу фильм жанра [жанр]», «рекомендации по жанру», «Можешь порекомендовать по жанру [жанр]»
    Жанр нужно понимать на русском и английском (комедия/Comedy, боевик/Action, драма/Drama, фантастика/Sci-Fi и т.д.).
    Если количество не указано — возвращай топ-10. Если указано — старайся выполнить (например, «покажи 5 комедий»).
    """

    genre_norm = genre.strip().lower()
    matches = []

    for movie in MOVIES_DB.values():
        genres = [g.strip().lower() for g in movie.get("Genre", "").split("|")]
        if genre_norm in genres:
            try:
                rating = float(movie["IMDB_Rating"])
            except:
                rating = 0
            matches.append((rating, movie))

    if not matches:
        return f"Фильмы жанра «{genre}» не найдены в топ-1000."

    matches.sort(reverse=True, key=lambda x: x[0])
    top10 = [m for _, m in matches[:10]]

    lines = [f"Топ-10 фильмов жанра «{genre.title()}»:\n"]
    for i, m in enumerate(top10, 1):
        lines.append(
            f"{i}. {m['Series_Title']} ({m['Released_Year']}) — IMDb: {m['IMDB_Rating']}/10"
        )

    return "\n".join(lines)


tools = [search_movie, compare_two_movies, get_movies_by_genre]


# Routes
class MessageRequest(BaseModel):
    title: str


@app.get("/")
async def root():
    return {"message": "CinemaChat API готов!"}


@app.get("/messages")
async def get_messages():
    return data


@app.post("/messages")
async def create_message(request: Request):
    body = await request.json()
    user_input = body.get("title", "").strip()
    if not user_input:
        return {"error": "Пустое сообщение"}, 400

    data.append({"title": user_input, "role": "user"})

    history = memory.load_memory_variables({})["history"]

    agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

    reasoning_steps = []
    final_answer = ""

    try:
        async for event in agent_executor.astream_events(
            {"input": user_input, "history": history}, version="v1"
        ):
            kind = event["event"]

            if kind == "on_chain_stream" and event.get("name") == "Agent":
                chunk = event["data"].get("chunk", {})
                thought = chunk.get("thought")
                if thought:
                    reasoning_steps.append({"type": "thought", "content": thought})

            if kind == "on_tool_start":
                reasoning_steps.append(
                    {
                        "type": "tool_start",
                        "tool": event["name"],
                        "args": event["data"].get("input", {}),
                    }
                )

            if kind == "on_tool_end":
                result = event["data"]["output"]
                reasoning_steps.append(
                    {"type": "observation", "content": str(result)[:1000]}
                )

            if kind == "on_chain_end" and event.get("name") == "AgentExecutor":
                output = event["data"].get("output", {})
                final_answer = (
                    output.get("output", "")
                    if isinstance(output, dict)
                    else str(output)
                )

        memory.save_context({"input": user_input}, {"output": final_answer})

        assistant_msg = {
            "title": final_answer or "Я не смог ответить...",
            "role": "assistant",
            "reasoning": reasoning_steps,
        }
        data.append(assistant_msg)

        return assistant_msg

    except Exception as e:
        error_msg = f"Ошибка: {str(e)}"
        error_response = {"title": error_msg, "role": "assistant"}
        data.append(error_response)
        return error_response
