# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install ffmpeg and other dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create directory for HLS segments
RUN mkdir -p static/live

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run gunicorn when the container launches
# Using 1 worker because we only have one FFmpeg process and we want to keep it simple
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "app:app"]
