FROM python:3.10-slim-bookworm

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

RUN apt update
RUN apt install -y git \
	libpq-dev \
	build-essential \
	poppler-utils

WORKDIR /app

# Create a directory to temporarily store speechtotext cmd input audio files
RUN mkdir /app/temp
# Create a directory to store voicelisten cmd output audio files
RUN mkdir /app/audio-output

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
RUN --mount=type=cache,target=/root/.cache/pip \
	--mount=type=bind,source=requirements.txt,target=requirements.txt \
	python -m pip install -r requirements.txt

# Copy the source code into the container.
COPY . .

CMD ["python", "bot.py"]
