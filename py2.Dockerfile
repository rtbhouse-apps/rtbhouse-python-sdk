FROM python:2.7.16-stretch

ARG UNAME=apps
ARG UID=1000
ARG GID=1000
ENV HOME="/home/$UNAME"
ENV WORKDIR="$HOME/code"
ENV PATH=$PATH:/home/$UNAME/.local/bin/

RUN groupadd -g $GID $UNAME && useradd -m -u $UID -g $GID -s /bin/bash $UNAME
RUN mkdir -p $WORKDIR && chown $UNAME:$UNAME $WORKDIR

USER $UNAME
WORKDIR $WORKDIR

COPY --chown=apps ./ $WORKDIR
RUN pip install --user -e .[dev]
CMD ["py.test", "--junitxml=./results/results.xml", "--color=no", "--cov-report", "term-missing", "--cov", "rtbhouse_sdk", "tests/"]