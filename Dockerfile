# Public site image for Fly.io app ms-erfurt.
# Build the pages first: python -m site_app.generator
FROM python:3.12-slim

WORKDIR /app
COPY site_app/__init__.py /app/site_app/__init__.py
COPY site_app/server.py /app/site_app/server.py
COPY site/dist /app/site/dist

ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8080
ENV SITE_DIST=/app/site/dist

EXPOSE 8080
USER nobody
CMD ["python", "-m", "site_app.server"]
