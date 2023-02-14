FROM --platform=linux/amd64 python:3.11-slim-buster

WORKDIR /moto

RUN apt-get update \
  && apt-get install gcc -y \
  && apt-get install make -y \
  && apt-get install vim -y \
  && apt-get install curl -y \
  && apt-get install default-libmysqlclient-dev -y \
  && apt-get install python-dev -y \
  && apt-get clean


RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false
RUN poetry install

COPY ./frontend ./frontend
COPY ./src ./src

EXPOSE 8000
CMD ["python", "./src/main.py"]
