# FastAPI optimized
# https://github.com/tiangolo/uvicorn-gunicorn-fastapi-docker
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-2020-06-06
COPY requirements.txt /app
RUN pip install --trusted-host pypi.python.org -r requirements.txt
COPY . /app

# need to add code for FastAPI generic
# insert code here

# Code to use if Flask is being run as main.
# FROM python:3.8
# WORKDIR /app
# COPY requirements.txt .
# RUN pip install --trusted-host pypi.python.org -r requirements.txt
# COPY . .
# CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app