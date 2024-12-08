ARG PYTHON_VERSION=3.10
FROM python:${PYTHON_VERSION}-slim AS builder

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
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
RUN --mount=type=cache,target=/root/.cache/pip \
	--mount=type=bind,source=requirements.txt,target=requirements.txt \
	python -m pip install -r requirements.txt

FROM python:${PYTHON_VERSION}-slim AS runtime

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1
# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

# NOTE: poppler-utils needed by pdf2image, libopus0 needed to join vc, ffmpeg needed by jsk vc yt cmd
RUN apt update && apt install -y --no-install-recommends \
	poppler-utils \
	libopus0 \
	ffmpeg \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create a directory to temporarily store speechtotext cmd input audio files
# NOTE: directory to store voicelisten cmd output audio files is mounted instead
RUN mkdir /app/temp

# Copy the source code into the container.
COPY . .

CMD ["python", "bot.py"]
