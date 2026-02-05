# Multi-stage image build to create a final image without uv

ARG PYTHON_VERSION=3.10
ARG BUILD_MODE=prod

# ---------------------------------------------------------------------------------------------------
# First, build the application in the `/app` directory.
# See `Dockerfile` for details.
FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-bookworm-slim AS builder

# Docs: https://superuser.com/questions/1405001/why-does-apt-do-not-store-downloaded-packages-anymore
RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/01keep-debs
# NOTE: poppler-utils needed by pdf2image, libopus0 needed to join vc, ffmpeg needed by jsk vc yt cmd
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    libopus0 \
    ffmpeg

# Enable bytecode compilation, Copy from the cache instead of linking since it's a mounted volume
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Disable Python downloads, because we want to use the system interpreter
# across both images. If using a managed Python version, it needs to be
# copied from the build image into the final image; see `standalone.Dockerfile`
# for an example.
ENV UV_PYTHON_DOWNLOADS=0

# Renew ARG: https://stackoverflow.com/a/53682110/16525120
ARG BUILD_MODE
# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/uv to speed up subsequent builds.
# Leverage a bind mount to pyproject.toml to avoid having to copy them into
# into this layer.
# Install the project's dependencies using the lockfile and settings
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    if [ "$BUILD_MODE" = "prod" ]; then \
        UV_NO_DEV=1 uv sync --locked --no-install-project; \
    else \
        uv sync --frozen --no-install-project; \
    fi

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

# ---------------------------------------------------------------------------------------------------
FROM builder

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# Renew ARG: https://stackoverflow.com/a/53682110/16525120
ARG BUILD_MODE
# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "$BUILD_MODE" = "prod" ]; then \
        UV_NO_DEV=1 uv sync --locked; \
    else \
        uv sync --frozen; \
    fi

# Run the application.
CMD ["python", "main.py"]
