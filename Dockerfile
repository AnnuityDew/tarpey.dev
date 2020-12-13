# Python image to use.
# FROM python:3.8

# Set the working directory to /app
# WORKDIR /app

# copy the requirements file used for dependencies
# COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the rest of the working directory contents into the container at /app
# COPY . .

# environment variables are set on Google Cloud
# CMD exec uvicorn app:app --port $PORT

# alternative
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-2020-06-06
WORKDIR /app
COPY requirements.txt .
RUN pip install --trusted-host pypi.python.org -r requirements.txt
COPY . .
