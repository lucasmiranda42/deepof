# Use a slim version of the Python base image
# To push a multi-platform build, use: docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 -t <image-name> --push .
FROM --platform=linux/amd64 python:3.10.14-slim as python-base

WORKDIR /

COPY pyproject.toml* .
COPY poetry.lock* .
COPY . .

# Combine apt-get commands and clean up after installations
RUN apt-get clean \
 && apt-get update \
 && apt-get -y upgrade \
 && apt-get --allow-releaseinfo-change update \
 && apt-get install -y --no-install-recommends gcc libgl1-mesa-dev libdatrie-dev ffmpeg git \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir pipx \
 && pipx install poetry==1.8.2 \
 && pipx ensurepath \
 && export PATH="$PATH:$HOME/.local/bin" \
 && poetry config virtualenvs.create false \
 && poetry install --no-interaction \
 && rm -r /root/.cache/

ENV PATH="./root/.local/pipx/venvs/poetry/bin:$PATH"

CMD [ "/bin/bash" ]
