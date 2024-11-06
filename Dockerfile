FROM cgr.dev/chainguard/python:latest-dev AS dev

WORKDIR /app

RUN python -m venv venv
ENV PATH="/app/venv/bin:$PATH"
COPY requirements.txt requirements.txt
RUN python -m pip install -r requirements.txt

FROM cgr.dev/chainguard/python:latest

WORKDIR /app

COPY bat2influx.py bat2influx.py
COPY --from=dev /app/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

ENTRYPOINT ["python", "bat2influx.py"]
