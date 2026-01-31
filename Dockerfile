ARG PYTHON_VERSION=3.10
ARG IMAGE=ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-bookworm-slim

# ---------------------------------------------------------------------------------------------------

FROM ${IMAGE} AS base

# Docs: https://superuser.com/questions/1405001/why-does-apt-do-not-store-downloaded-packages-anymore
RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/01keep-debs
# NOTE: poppler-utils needed by pdf2image, libopus0 needed to join vc, ffmpeg needed by jsk vc yt cmd
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    libopus0 \
    ffmpeg

# TODO: WE MIGHT NOT WANT THIS IN DEVCONTAINER
# Install the project into `/app`
WORKDIR /app

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Omit development dependencies
# ENV UV_NO_DEV=1

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/uv to speed up subsequent builds.
# Leverage a bind mount to pyproject.toml to avoid having to copy them into
# into this layer.

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --locked --no-install-project

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
# TODO: WE MIGHT NOT WANT THIS IN DEVCONTAINER
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# ---------------------------------------------------------------------------------------------------

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Run the application.
CMD ["uv", "run", "main.py"]
