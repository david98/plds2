FROM python:3.9

SHELL ["/bin/bash", "-c"]

WORKDIR /plds2

RUN apt-get update && apt-get install -y python3.9-venv
ENV VIRTUAL_ENV=/plds2/venv
RUN python3 -m venv ./venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY config.py config.py
COPY main.py main.py
ENTRYPOINT ["python3", "main.py"]