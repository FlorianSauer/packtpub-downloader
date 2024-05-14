FROM python:3.10

ARG PUID=1000
ARG PGID=1000
ARG UNAME=testuser

ENV EMAIL="" \
    PASSWORD="" \
    FILE_TYPES="pdf,mobi,epub,code,video"

WORKDIR /app

COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd -g $PGID -o $UNAME && \
    useradd -m -u $PUID -g $PGID -o -s /bin/bash $UNAME

RUN mkdir /app/books && \
    chown $PUID:$PGID /app/books

COPY ./src /app
COPY ./entrypoint.sh /app

USER $UNAME

CMD bash entrypoint.sh