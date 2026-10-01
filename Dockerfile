FROM python:3.12-slim

WORKDIR /app
COPY app.py faq.json ./
RUN useradd --system --uid 10001 bot
USER 10001

ENV PYTHONUNBUFFERED=1
CMD ["python", "app.py"]
