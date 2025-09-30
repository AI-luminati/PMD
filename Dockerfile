# Base image with Java
FROM openjdk:17-slim

# Install Python + pip + unzip
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip unzip \
    && rm -rf /var/lib/apt/lists/*

# Set PMD environment
ENV PMD_VERSION=7.17.0
ENV PMD_DIR=/opt/pmd-bin-$PMD_VERSION
ENV PATH=$PMD_DIR/bin:$PATH

# Copy PMD zip locally and unzip
COPY pmd-bin-7.17.0.zip /tmp/
RUN unzip /tmp/pmd-bin-7.17.0.zip -d /opt/ && rm /tmp/pmd-bin-7.17.0.zip

# Copy Flask app
WORKDIR /app
COPY . /app

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 5000

# Start Flask
CMD ["python3", "app.py"]
