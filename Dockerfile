FROM python:3.10-slim-bookworm AS builder

# Prevents Python from writing pyc files.
# ? Will this only be effective for the builder and not runtime?
# ? Seems like it's scoped per build stage: https://github.com/moby/moby/issues/37345#issuecomment-400245466
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt update && apt install -y --no-install-recommends \
	git \
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

FROM python:3.10-slim-bookworm AS runtime

COPY --from=builder /opt/venv /opt/venv

RUN apt update && apt install -y --no-install-recommends \
	poppler-utils \
	libopus0 \
	ffmpeg \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create a directory to temporarily store speechtotext cmd input audio files
RUN mkdir /app/temp

# Create a directory to store voicelisten cmd output audio files
RUN mkdir /app/audio-output

# Copy the source code into the container.
COPY . .

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

ENV PATH="/opt/venv/bin:$PATH"

CMD ["python", "bot.py"]
