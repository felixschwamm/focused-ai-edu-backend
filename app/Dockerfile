# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Install PostgreSQL client development headers
RUN apt-get update && apt-get install -y libpq-dev gcc

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV MODULE_NAME="main"
ENV VARIABLE_NAME="app"
ENV HOST="0.0.0.0"

# Run uvicorn when the container launches
CMD uvicorn $MODULE_NAME:$VARIABLE_NAME --host $HOST --reload
