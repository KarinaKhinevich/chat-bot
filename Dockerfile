FROM python:3.11-slim

WORKDIR /chat_bot

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy only pyproject.toml and poetry.lock first for better cache
COPY pyproject.toml poetry.lock ./

# Configure Poetry to not use virtualenvs
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# Copy the rest of the application
COPY ./chat_bot ./chat_bot

# Expose port
EXPOSE 8000

# Start the app
CMD ["uvicorn", "chat_bot.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
