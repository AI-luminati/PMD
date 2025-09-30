# Base image with Java
FROM openjdk:17-slim

# Install Python3, pip, curl, unzip
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip curl unzip \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip to latest
RUN python3 -m pip install --upgrade pip

# Set PMD version
ENV PMD_VERSION=7.17.0
ENV PMD_DIR=/opt/pmd-dist-$PMD_VERSION
ENV PATH=$PMD_DIR/bin:$PATH

# Download PMD correctly
RUN curl -L -O https://github.com/pmd/pmd/releases/download/pmd_releases/7.17.0/pmd-dist-7.17.0-bin.zip \
    && unzip pmd-dist-7.17.0-bin.zip -d /opt/ \
    && rm pmd-dist-7.17.0-bin.zip

# Copy Flask app
WORKDIR /app
COPY . /app

# Install Python dependencies
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 5000

# Start Flask
CMD ["python3", "app.py"]
