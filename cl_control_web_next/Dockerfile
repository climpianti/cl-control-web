FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /opt/cl-control-web
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd -r -u 10001 -d /opt/cl-control-web clcontrol
COPY --chown=10001:10001 app/ ./app/
USER 10001:10001
EXPOSE 8099
CMD ["python","app/server.py"]
