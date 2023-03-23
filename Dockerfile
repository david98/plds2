FROM python:3.9

SHELL ["/bin/bash", "-c"]

WORKDIR /plds2

RUN \
    --mount=type=cache,target=/var/cache/apt  \
    \apt-get update && apt-get install -y python3.9-venv
ENV VIRTUAL_ENV=/plds2/venv
RUN python3 -m venv ./venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN \
    --mount=type=cache,target=/root/.cache \
    pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN \
    --mount=type=cache,target=/root/.cache \
    pip install -r requirements.txt

COPY config.py config.py
COPY main.py main.py
ENTRYPOINT ["python3", "main.py"]