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
# /data is an externally mounted Supervisor volume and starts root-owned.
# Fix its ownership before dropping privileges; the web process never runs as root.
CMD ["/bin/sh", "-c", "install -d -m 700 -o 10001 -g 10001 /data && exec gosu clcontrol python app/server.py"]
