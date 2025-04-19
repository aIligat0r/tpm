FROM python:3.12-slim

ENV WORKDIR="/app"

WORKDIR $WORKDIR

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \

    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_HOME='/usr/local'

RUN pip install poetry

COPY . $WORKDIR

RUN poetry install --only main && rm -rf $POETRY_CACHE_DIR

ENTRYPOINT ["telegram-pm"]
