# Use slim Python image
FROM python:3.11-slim

# Set PMD version
ENV PMD_VERSION=7.17.0
ENV PMD_DIR=/opt/pmd-bin-$PMD_VERSION
ENV PATH=$PMD_DIR/bin:$PATH

# Install Java, wget, unzip
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jdk wget unzip \
    && rm -rf /var/lib/apt/lists/*

# Download PMD
RUN wget https://github.com/pmd/pmd/releases/download/pmd_releases%2F$PMD_VERSION/pmd-bin-$PMD_VERSION.zip \
    && unzip pmd-bin-$PMD_VERSION.zip -d /opt/ \
    && rm pmd-bin-$PMD_VERSION.zip

# Copy Flask app
WORKDIR /app
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 5000

# Run Flask app
CMD ["python", "app.py"]
