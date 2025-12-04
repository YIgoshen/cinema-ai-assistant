Чат-бот на базе **GPT-4o-mini + LangChain + FastAPI + Next.js**

**Tools:**

- search_movie
- compare_two_movies
- get_movies_by_genre

## Как запустить проект локально

### 1. Открыть данную папку или склонировать репозиторией.

```bash
git clone https://github.com/YIgoshen/cinema-ai-assistant
cd cinema-ai-assistant
```

### 2. Создаём и заполняем .env файл (в корне проекта)

```bash
cp .env.example .env
```

Содержимое .env (обязательные переменные):

# OpenAI (обязательно)

```bash
OPENAI_API_KEY=sk-ваш_ключ_от_openai

# OMDB API — для поиска фильмов, которых нет в локальной базе (рекомендуется)
OMDB_API_KEY=ваш_ключ_с_omdbapi.com
```

### 3. Устанавливаем и запускаем бэкенд

# Создаём виртуальное окружение (рекомендуется)

```bash
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Устанавливаем зависимости
pip install -r requirements.txt

# Запускаем FastAPI сервер
uvicorn main:app --reload --port=8000
```

Бэкенд будет доступен по адресу: http://127.0.0.1:8000/api/v1

### 4. Запускаем фронтенд (Next.js)

Отдельное терминальное окно:

```bash
cd frontend
```

# Устанавливаем зависимости

```bash
npm install
# или
yarn
# или
pnpm i
```

# Создаём .env.local во frontend папке

```bash
cp .env.local.example .env.local
```

Содержимое frontend/.env.local:

```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1
```

# Запускаем dev-сервер

```bash
npm run dev

# или yarn dev
```

Открой в браузере: http://localhost:3000
