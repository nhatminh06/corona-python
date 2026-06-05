# Build stage — installs Python dependencies through Nexus pypi-proxy
FROM harbor.lab:8080/library/python:3.11-slim AS build

WORKDIR /build

ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1

# pip.conf is fetched by Jenkins from Nexus build-config before docker build
COPY pip.conf /etc/pip.conf

COPY requirements.txt .
RUN python -m pip install --prefix=/install -r requirements.txt


# Runtime stage
FROM harbor.lab:8080/library/python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

RUN useradd -u 1000 -m appuser

COPY --from=build /install /usr/local
COPY app.py /app/app.py

USER appuser

EXPOSE 8080

CMD ["python", "app.py"]
