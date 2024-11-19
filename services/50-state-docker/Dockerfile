# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set environment variables to reduce the need for user prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install Chrome dependencies, Chrome, and wget
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxi6 \
    libxtst6 \
    libappindicator3-1 \
    libxrandr2 \
    xdg-utils \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get install -y ./google-chrome.deb && \
    rm google-chrome.deb

# Install Chromedriver
RUN CHROME_DRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
    wget -q "https://chromedriver.storage.googleapis.com/${CHROME_DRIVER_VERSION}/chromedriver_linux64.zip" && \
    unzip chromedriver_linux64.zip -d /usr/local/bin/ && \
    rm chromedriver_linux64.zip && \
    chmod +x /usr/local/bin/chromedriver

# Install Selenium
RUN pip install selenium

# Set display port to avoid errors
ENV DISPLAY=:99

# Copy the current directory contents into the container at /app
COPY . /app

RUN chmod 600 /app/sbx-kendra-8e724bd9a0ce.json

# Install libmagic
RUN apt-get update && \
    apt-get install -y libmagic1 && \
    rm -rf /var/lib/apt/lists/*

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV NAME=World

# Run app.py when the container launches
CMD ["python", "scraper.py"]
