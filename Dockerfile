FROM python:3.10.8-slim-buster

ARG UNAME=apps
ARG UID=1000
ARG GID=1000
ENV POETRY_HOME=/opt/poetry
ENV WORKDIR=/home/$UNAME/code
ENV PATH=$PATH:/home/$UNAME/.local/bin/

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -fr /var/lib/apt/lists/*

RUN python -m pip install --upgrade --no-cache-dir pip==22.2.2

# Install Poetry
RUN curl -sSl https://install.python-poetry.org | python - --version 1.2.1 \
    && ln -s ${POETRY_HOME}/bin/poetry /usr/local/bin/poetry

RUN groupadd -g $GID $UNAME \
    && useradd -m -u $UID -g $GID -s /bin/bash $UNAME \
    && mkdir -p $WORKDIR \
    && chown $UNAME:$UNAME $WORKDIR

USER $UNAME
WORKDIR $WORKDIR

COPY --chown=apps ./ $WORKDIR
RUN poetry install --no-root
CMD ["poetry", "run", "python", "-m", "pytest","--color=no", \
    "--cov-report=term-missing", "--cov=rtbhouse_sdk", "tests/"]
