# ---- Stage 1: Build ----
FROM hseeberger/scala-sbt:17.0.2_1.6.2_2.13.8 AS builder

WORKDIR /app

# Copy build definition first for layer caching — dependencies only re-download if build files change
COPY project/ project/
COPY build.sbt .

# Pre-fetch dependencies
RUN sbt update

# Copy source and assemble fat JAR
COPY src/ src/
RUN sbt assembly

# ---- Stage 2: Runtime ----
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app

COPY --from=builder /app/target/scala-2.13/forex-assembly.jar app.jar

EXPOSE 9090

ENTRYPOINT ["java", "-jar", "app.jar"]
