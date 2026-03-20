# Build v5 — eclipse-temurin:17 base (JDK pre-installed), add Python
FROM eclipse-temurin:17-jdk-jammy

# Install Python 3.11
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-dev \
    python3-pip \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3 \
    && ln -sf /usr/bin/python3.11 /usr/bin/python

# Verify both Java and Python
RUN java -version && javac -version && python3 --version

WORKDIR /app

# Copy and install Python dependencies
COPY backend/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Java env (already set by base image, but be explicit)
ENV JAVA_HOME=/opt/java/openjdk
ENV PATH="$JAVA_HOME/bin:$PATH"

EXPOSE 8000

CMD ["python3", "start.py"]
