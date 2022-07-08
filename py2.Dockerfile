FROM python:2.7.18-stretch

ARG UNAME=apps
ARG UID=1000
ARG GID=1000
ENV POETRY_HOME=/opt/poetry
ENV HOMEDIR=/home/$UNAME
ENV WORKDIR=/home/$UNAME/code
ENV PATH=$PATH:/home/$UNAME/.local/bin/

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -fr /var/lib/apt/lists/*

RUN python -m pip install --upgrade --no-cache-dir pip==20.3.4

# Install Poetry
RUN export POETRY_VERSION=1.1.5 \
    && curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python \
    && chmod a+x ${POETRY_HOME}/bin/poetry \
    && ln -s ${POETRY_HOME}/bin/poetry /usr/local/bin/poetry \
    && poetry config virtualenvs.create false \
    && cp -r ~/.config/ /etc/skel/

RUN groupadd -g $GID $UNAME \
    && useradd -m -u $UID -g $GID -s /bin/bash $UNAME \
    && mkdir -p $HOMEDIR/.local/lib/python2.7/site-packages \
    && mkdir -p $HOMEDIR/.local/bin \
    && chown -R $UID:$GID $HOMEDIR/.local \
    && mkdir -p $WORKDIR \
    && chown $UNAME:$UNAME $WORKDIR

USER $UNAME
WORKDIR $WORKDIR

COPY --chown=apps ./ $WORKDIR
RUN poetry install -vvv --no-root
CMD ["poetry", "run", "python", "-m", "pytest", "--junitxml=./results/results.xml", "--color=no", \
    "--cov-report=term-missing", "--cov=rtbhouse_sdk", "tests/"]
