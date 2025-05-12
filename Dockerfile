ARG IMAGE=ghcr.io/astral-sh/uv:python3.10-bookworm-slim

# -- 1st stage --------------------------------------------------------------------------------------

FROM ${IMAGE} AS builder

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1
# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# NOTE: libpq-dev and build-essential is needed for psycopg2 to build (SQLAlchemy dependency)
RUN apt update && apt install -y --no-install-recommends \
	# git \
	libpq-dev \
	build-essential \
	&& rm -rf /var/lib/apt/lists/*

# Got the multi-stage venv technique from https://pythonspeed.com/articles/multi-stage-docker-python/
RUN uv venv /opt/venv
# Use the virtual environment automatically
ENV VIRTUAL_ENV=/opt/venv
# Place entry points in the environment at the front of the path
ENV PATH="/opt/venv/bin:$PATH"

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
RUN --mount=type=cache,target=/root/.cache/uv \
	--mount=type=bind,source=requirements.txt,target=requirements.txt \
	uv pip install -r requirements.txt

# -- 2nd stage --------------------------------------------------------------------------------------

FROM ${IMAGE} AS runtime

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1
# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

COPY --from=builder /opt/venv /opt/venv
# Use the virtual environment automatically
ENV VIRTUAL_ENV=/opt/venv
# Place entry points in the environment at the front of the path
ENV PATH="/opt/venv/bin:$PATH"

# NOTE: poppler-utils needed by pdf2image, libopus0 needed to join vc, ffmpeg needed by jsk vc yt cmd
RUN apt update && apt install -y --no-install-recommends \
	poppler-utils \
	libopus0 \
	ffmpeg \
	&& rm -rf /var/lib/apt/lists/*

# -- prod stage -------------------------------------------------------------------------------------

FROM runtime AS prod

WORKDIR /app

# Copy the source code into the container.
COPY . .

CMD ["python", "bot.py"]
