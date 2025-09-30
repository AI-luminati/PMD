# Use official OpenJDK base (Java already installed)
FROM openjdk:17-slim

# Install Python 3.11 + pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip wget unzip \
    && rm -rf /var/lib/apt/lists/*

# Set PMD version
ENV PMD_VERSION=7.17.0
ENV PMD_DIR=/opt/pmd-bin-$PMD_VERSION
ENV PATH=$PMD_DIR/bin:$PATH

# Download PMD
RUN wget https://github.com/pmd/pmd/releases/download/pmd_releases%2F$PMD_VERSION/pmd-bin-$PMD_VERSION.zip \
    && unzip pmd-bin-$PMD_VERSION.zip -d /opt/ \
    && rm pmd-bin-$PMD_VERSION.zip

# Copy Flask app
WORKDIR /app
COPY . /app

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 5000

# Start Flask app
CMD ["python3", "app.py"]
