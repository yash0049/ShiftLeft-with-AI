FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies first so edits to application code don't invalidate this layer.
COPY requirements.txt requirements-docker.txt ./
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY . .

# Run as a non-root user. /data is created here so that the named volume mounted
# over it at runtime inherits this ownership and stays writable.
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /app /data
USER appuser

# Four slashes: sqlite:// + the absolute path /data/securetrack.db
ENV DATABASE_URL=sqlite:////data/securetrack.db

EXPOSE 5000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
    CMD python -c "import urllib.request as u, sys; sys.exit(0 if u.urlopen('http://127.0.0.1:5000/health', timeout=2).status == 200 else 1)"

# run.py already exposes a module-level `app`; its dev server sits behind a
# __main__ guard, so importing it here is safe.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "run:app"]
