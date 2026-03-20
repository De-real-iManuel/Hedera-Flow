# Build v4 — JDK via eclipse-temurin base image, no apt issues
FROM python:3.11-slim

WORKDIR /app

# Install JDK 17 + build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    wget \
    gnupg \
    && wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | gpg --dearmor -o /usr/share/keyrings/adoptium.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/adoptium.gpg] https://packages.adoptium.net/artifactory/deb $(. /etc/os-release && echo $VERSION_CODENAME) main" > /etc/apt/sources.list.d/adoptium.list \
    && apt-get update && apt-get install -y --no-install-recommends temurin-17-jdk \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/temurin-17-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

# Verify Java
RUN java -version && javac -version

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (from repo root, backend/ subdir)
COPY backend/ .

# Set runtime Java environment variables
ENV JAVA_HOME=/usr/lib/jvm/temurin-17-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

# Expose port
EXPOSE 8000

# Start command
CMD ["python3", "start.py"]
