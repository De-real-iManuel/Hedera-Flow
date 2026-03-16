FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including full JDK (required for hedera-sdk-py)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    openjdk-17-jdk \
    openjdk-17-jdk-headless \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME environment variable and add to PATH
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"
ENV JDK_HOME=$JAVA_HOME
ENV CLASSPATH="$JAVA_HOME/lib/*:."

# Verify Java installation
RUN java -version && javac -version

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy startup script
COPY start.py .
RUN chmod +x start.py

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Start command
CMD ["python3", "start.py"]