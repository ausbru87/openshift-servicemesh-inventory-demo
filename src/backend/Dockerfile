# Backend Dockerfile for OpenShift Service Mesh Inventory Demo
# Multi-stage build for optimized production image

# Build stage
FROM registry.access.redhat.com/ubi8/python-39 AS builder

# Switch to root for package installation
USER root

# Install system dependencies
RUN dnf update -y && \
    dnf install -y \
        gcc \
        gcc-c++ \
        postgresql-devel \
        python39-devel \
    && dnf clean all \
    && rm -rf /var/cache/dnf

# Switch to application user
USER 1001

# Set working directory
WORKDIR /opt/app-root/src

# Copy requirements first for better caching
COPY --chown=1001:0 requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM registry.access.redhat.com/ubi8/python-39

# Install runtime dependencies only
USER root
RUN dnf update -y && \
    dnf install -y postgresql-libs && \
    dnf clean all && \
    rm -rf /var/cache/dnf

# Create application directory and set permissions
RUN mkdir -p /opt/app-root/src && \
    chown -R 1001:0 /opt/app-root && \
    chmod -R g+rw /opt/app-root

# Switch to application user
USER 1001

# Set working directory
WORKDIR /opt/app-root/src

# Copy installed packages from builder stage
COPY --from=builder --chown=1001:0 /opt/app-root/lib/python3.9/site-packages/ \
     /opt/app-root/lib/python3.9/site-packages/

# Copy application code
COPY --chown=1001:0 app.py .
COPY --chown=1001:0 config.py .

# Set environment variables
ENV FLASK_APP=app.py \
    FLASK_ENV=production \
    PYTHONPATH=/opt/app-root/src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/app-root/bin:$PATH"

# Create non-root user directories
RUN mkdir -p /opt/app-root/src/logs && \
    chmod g+w /opt/app-root/src/logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Security: Run as non-root user
USER 1001

# Expose port
EXPOSE 5000

# Add labels for OpenShift and Service Mesh
LABEL name="inventory-backend" \
      version="1.0.0" \
      description="OpenShift Service Mesh Inventory Demo Backend" \
      maintainer="OpenShift Demo Team" \
      io.k8s.description="Flask backend for Service Mesh inventory demo" \
      io.k8s.display-name="Inventory Backend" \
      io.openshift.expose-services="5000:http" \
      io.openshift.tags="python,flask,postgresql,service-mesh,demo" \
      vendor="Red Hat" \
      component="backend" \
      service-mesh.enabled="true" \
      service-mesh.version="2.6"

# Start the application
CMD ["python", "app.py"]