FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY ./pyproject.toml ./uv.lock ./README.md ./

# Install third-party deps first for better layer caching.
RUN uv sync --frozen --no-dev --no-install-project

COPY ./src ./src
COPY ./fm_views ./fm_views

RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uv", "run", "football-manager-data-ui"]
