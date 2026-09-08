FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY exporter.py .

RUN addgroup --system exporter \
    && adduser --system --ingroup exporter exporter \
    && chown -R exporter:exporter /app

USER exporter

EXPOSE 8000

CMD ["python", "exporter.py"]
