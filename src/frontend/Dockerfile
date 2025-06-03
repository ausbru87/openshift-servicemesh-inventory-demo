# Frontend Dockerfile for OpenShift Service Mesh Inventory Demo
# Multi-stage build for optimized production image

# Build stage - prepare static assets
FROM registry.access.redhat.com/ubi8/nodejs-18 AS builder

# Switch to root for package installation
USER root

# Install build dependencies
RUN dnf update -y && \
    dnf install -y \
        git \
        gzip \
    && dnf clean all \
    && rm -rf /var/cache/dnf

# Switch to application user
USER 1001

# Set working directory
WORKDIR /opt/app-root/src

# Copy source files
COPY --chown=1001:0 index.html .
COPY --chown=1001:0 styles.css .
COPY --chown=1001:0 script.js .

# Create optimized build
RUN mkdir -p build && \
    # Copy HTML file
    cp index.html build/ && \
    # Minify CSS (basic minification)
    sed '/^[[:space:]]*\/\*/,/\*\//d; /^[[:space:]]*$/d; s/[[:space:]]*{[[:space:]]*/{/g; s/[[:space:]]*}[[:space:]]*/}/g' styles.css > build/styles.css && \
    # Minify JavaScript (basic minification) 
    sed '/^[[:space:]]*\/\*/,/\*\//d; /^[[:space:]]*\/\//d; /^[[:space:]]*$/d' script.js > build/script.js && \
    # Gzip static assets for better compression
    gzip -k build/styles.css && \
    gzip -k build/script.js

# Production stage
FROM registry.access.redhat.com/ubi8/nginx-120

# Switch to root for configuration
USER root

# Install additional tools for health checks
RUN dnf update -y && \
    dnf install -y curl && \
    dnf clean all && \
    rm -rf /var/cache/dnf

# Create required directories and set permissions
RUN mkdir -p /var/cache/nginx/client_temp && \
    mkdir -p /var/cache/nginx/proxy_temp && \
    mkdir -p /var/cache/nginx/fastcgi_temp && \
    mkdir -p /var/cache/nginx/uwsgi_temp && \
    mkdir -p /var/cache/nginx/scgi_temp && \
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

# Copy optimized static files from builder
COPY --from=builder --chown=1001:0 /opt/app-root/src/build/ /usr/share/nginx/html/

# Copy nginx configuration
COPY --chown=1001:0 nginx.conf /etc/nginx/nginx.conf

# Create error pages
RUN echo '<!DOCTYPE html>
<html>
<head><title>404 Not Found</title></head>
<body>
<h1>404 Not Found</h1>
<p>The requested resource was not found on this server.</p>
<p><a href="/">Return to Inventory Demo</a></p>
</body>
</html>' > /usr/share/nginx/html/404.html && \
    echo '<!DOCTYPE html>
<html>
<head><title>Service Unavailable</title></head>
<body>
<h1>Service Temporarily Unavailable</h1>
<p>The service is temporarily unavailable. Please try again later.</p>
<p><a href="/">Return to Inventory Demo</a></p>
</body>
</html>' > /usr/share/nginx/html/50x.html

# Create a service worker for PWA capabilities (optional)
RUN echo 'self.addEventListener("fetch", function(event) {
  // Basic service worker for caching
  if (event.request.destination === "image" || 
      event.request.destination === "style" || 
      event.request.destination === "script") {
    event.respondWith(
      caches.match(event.request).then(function(response) {
        return response || fetch(event.request);
      })
    );
  }
});' > /usr/share/nginx/html/sw.js

# Set proper file permissions
RUN chown -R 1001:0 /usr/share/nginx/html && \
    chmod -R g+r /usr/share/nginx/html

# Switch to application user
USER 1001

# Set environment variables
ENV NGINX_USER=nginx \
    NGINX_WORKER_PROCESSES=auto \
    NGINX_WORKER_CONNECTIONS=1024 \
    NGINX_KEEPALIVE_TIMEOUT=65

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Security: Run as non-root user
USER 1001

# Expose port
EXPOSE 8080

# Add labels for OpenShift and Service Mesh
LABEL name="inventory-frontend" \
      version="1.0.0" \
      description="OpenShift Service Mesh Inventory Demo Frontend" \
      maintainer="OpenShift Demo Team" \
      io.k8s.description="Nginx frontend for Service Mesh inventory demo" \
      io.k8s.display-name="Inventory Frontend" \
      io.openshift.expose-services="8080:http" \
      io.openshift.tags="nginx,html,javascript,service-mesh,demo" \
      vendor="Red Hat" \
      component="frontend" \
      service-mesh.enabled="true" \
      service-mesh.version="2.6" \
      app.openshift.io/runtime="nginx" \
      app.openshift.io/runtime-version="1.20"

# Start nginx
CMD ["nginx", "-g", "daemon off;"]