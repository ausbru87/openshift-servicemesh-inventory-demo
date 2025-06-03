# Frontend Dockerfile for OpenShift Service Mesh Inventory Demo
FROM registry.access.redhat.com/ubi8/nginx-120

# Switch to root for setup
USER root

# Install curl for health checks
RUN dnf update -y && \
    dnf install -y curl && \
    dnf clean all && \
    rm -rf /var/cache/dnf

# Create required directories and set permissions
RUN mkdir -p /var/cache/nginx && \
    mkdir -p /var/log/nginx && \
    mkdir -p /tmp/nginx && \
    chown -R 1001:0 /var/cache/nginx && \
    chown -R 1001:0 /var/log/nginx && \
    chown -R 1001:0 /tmp && \
    chown -R 1001:0 /etc/nginx && \
    chown -R 1001:0 /usr/share/nginx/html && \
    chmod -R g+rwX /var/cache/nginx && \
    chmod -R g+rwX /var/log/nginx && \
    chmod -R g+rwX /tmp && \
    chmod -R g+rwX /etc/nginx && \
    chmod -R g+rwX /usr/share/nginx/html

# Copy static files from source
COPY --chown=1001:0 index.html /usr/share/nginx/html/
COPY --chown=1001:0 styles.css /usr/share/nginx/html/
COPY --chown=1001:0 script.js /usr/share/nginx/html/

# Copy nginx configuration
COPY --chown=1001:0 nginx.conf /etc/nginx/nginx.conf

# Create simple error pages
COPY --chown=1001:0 404.html /usr/share/nginx/html/
COPY --chown=1001:0 50x.html /usr/share/nginx/html/

# Set proper ownership
RUN chown -R 1001:0 /usr/share/nginx/html

# Switch to non-root user
USER 1001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Labels
LABEL name="inventory-frontend" \
      version="1.0.0" \
      description="OpenShift Service Mesh Inventory Demo Frontend" \
      io.k8s.description="Nginx frontend for Service Mesh inventory demo" \
      io.openshift.expose-services="8080:http" \
      service-mesh.enabled="true"

# Start nginx
CMD ["nginx", "-g", "daemon off;"]