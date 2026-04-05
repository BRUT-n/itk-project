# 1. Берем легкий образ с Python 3.12
FROM python:3.12-slim

# 2. Устанавливаем uv (копируем бинарник из официального образа uv)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. Указываем рабочую папку внутри контейнера
WORKDIR /app

# 4. Копируем файлы зависимостей
# Это pyproject.toml и uv.lock, которые создал твой uv
COPY pyproject.toml uv.lock ./

# 5. Устанавливаем все библиотеки (быстро и без кэша, чтобы образ был легче)
RUN uv sync --frozen --no-cache

# 6. Копируем весь остальной код (папку app, .env и т.д.)
COPY . .

RUN chmod +x /app/entrypoint.sh

# 7. Команда для запуска
# Используем --host 0.0.0.0, чтобы Docker "выпустил" сервер наружу
ENTRYPOINT ["/app/entrypoint.sh"]