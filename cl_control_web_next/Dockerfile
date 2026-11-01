FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /opt/cl-control-web
COPY requirements.txt ./
RUN apt-get update && apt-get install -y --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt \
    && useradd -r -u 10001 -d /opt/cl-control-web clcontrol
COPY --chown=10001:10001 app/ ./app/
EXPOSE 8099
# Initialize private data/configuration permissions before dropping privileges.
# The web server runs as clcontrol; configuration is neither copied nor printed.
CMD ["python", "app/startup.py"]
