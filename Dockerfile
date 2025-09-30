# Base image with Java
FROM openjdk:17-slim

# Install Python, pip, curl, unzip
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip curl unzip \
    && rm -rf /var/lib/apt/lists/*

# Set PMD version
ENV PMD_VERSION=7.17.0
ENV PMD_DIR=/opt/pmd-bin-$PMD_VERSION
ENV PATH=$PMD_DIR/bin:$PATH

# Download PMD reliably using curl
RUN curl -L -O https://github.com/pmd/pmd/releases/download/pmd_releases/7.17.0/pmd-bin-7.17.0.zip \
    && unzip pmd-bin-7.17.0.zip -d /opt/ \
    && rm pmd-bin-7.17.0.zip

# Copy Flask app
WORKDIR /app
COPY . /app

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 5000

# Start Flask app
CMD ["python3", "app.py"]
