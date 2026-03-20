# Build v7 — eclipse-temurin:17-jdk-jammy, root dir = backend/
FROM eclipse-temurin:17-jdk-jammy

# Set JAVA_HOME and JVM_PATH early so pyjnius can find libjvm.so
# eclipse-temurin puts JDK at /opt/java/openjdk
ENV JAVA_HOME=/opt/java/openjdk
ENV PATH="$JAVA_HOME/bin:$PATH"
ENV JVM_PATH=/opt/java/openjdk/lib/server/libjvm.so

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-dev \
    python3-pip \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3 \
    && ln -sf /usr/bin/python3.11 /usr/bin/python

# Verify Java + Python are available
RUN java -version && javac -version && python3 --version

# Verify libjvm.so exists at the expected path
RUN test -f /opt/java/openjdk/lib/server/libjvm.so && echo "✅ libjvm.so found" || (find /opt/java -name "libjvm.so" && exit 1)

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python3", "start.py"]
