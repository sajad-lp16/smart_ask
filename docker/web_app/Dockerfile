FROM python:3.12.2-slim-bookworm AS python

# Stage1: build our dependency wheels
FROM python AS python-build-stage

ARG BUILD_ENVIRONMENT=production

RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential
COPY ./requirements.txt .
RUN pip wheel --wheel-dir /usr/src/app/wheels -r requirements.txt

# Stage2: run stage
FROM python AS python-run-stage

ARG BUILD_ENVIRONMENT=production
ARG APP_HOME=/app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUBUFFERED=1 \
    BUILD_ENVIRONMENT=${BUILD_ENVIRONMENT}

WORKDIR ${APP_HOME}

RUN apt-get update && apt-get install --no-install-recommends -y \
    sudo git bash-completion vim ssh \
    gettext \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup web_app && \
    adduser --ingroup web_app web_app

COPY --from=python-build-stage /usr/src/app/wheels /wheels/
RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
    && rm -rf /wheels/

COPY --chown=web_app:web_app ./docker/web_app/entrypoint.sh /entrypoint.sh
COPY --chown=web_app:web_app ./docker/web_app/start.sh /start.sh

RUN sed -i 's/\r$//g' /entrypoint.sh /start.sh  && \
    chmod +x /entrypoint.sh /start.sh

COPY --chown=web_app:web_app . ${APP_HOME}

USER web_app

ENTRYPOINT ["/entrypoint.sh"]