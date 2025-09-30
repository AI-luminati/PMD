FROM openjdk:17-slim

# Install Python, pip, bash, unzip, curl, build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip bash unzip curl build-essential python3-dev libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python3 -m pip install --upgrade pip setuptools wheel

# Copy Flask app
WORKDIR /app
COPY . /app

# Install Python dependencies
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Expose Flask port
EXPOSE 5000

# Start Flask app
CMD ["python3", "app.py"]
