FROM harbor.lab:8080/library/python:3.11-slim
WORKDIR /app

RUN mkdir -p /root/.pip
COPY pip.conf /root/.pip/pip.conf

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -r -u 1000 appuser
USER appuser

EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]

