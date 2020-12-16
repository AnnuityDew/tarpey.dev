# Python image to use.
FROM python:3.8

# Set the working directory to /app
WORKDIR /app

# copy the requirements file used for dependencies
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the rest of the working directory contents into the container at /app
COPY . .

# get it going!
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app

# FastAPI alternative
# FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-2020-06-06
# WORKDIR /app
# COPY requirements.txt .
# RUN pip install --trusted-host pypi.python.org -r requirements.txt
# COPY . .
