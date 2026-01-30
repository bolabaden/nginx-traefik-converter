# nginx-proxy Documentation

nginx-proxy sets up a container running nginx and docker-gen. docker-gen generates reverse proxy configs for nginx and reloads nginx when containers are started and stopped.

## Overview

nginx-proxy is an automated nginx reverse proxy for Docker containers using docker-gen. It provides:

- Automated reverse proxy configuration for Docker containers
- Virtual host routing based on environment variables
- SSL termination and certificate management
- Load balancing across multiple containers
- Zero-downtime deployments

## Basic Usage

To run nginx-proxy:

```bash
docker run --detach \
    --name nginx-proxy \
    --publish 80:80 \
    --volume /var/run/docker.sock:/tmp/docker.sock:ro \
    nginxproxy/nginx-proxy:1.7
```

Then start any containers you want proxied with a `VIRTUAL_HOST` environment variable:

```bash
docker run --detach \
    --name your-proxied-app \
    --env VIRTUAL_HOST=foo.bar.com \
    nginx
```

## Key Environment Variables

### VIRTUAL_HOST
- **Purpose**: Defines the hostname(s) for routing
- **Example**: `VIRTUAL_HOST=example.com`
- **Multiple hosts**: `VIRTUAL_HOST=example.com,www.example.com`
- **Wildcards**: `VIRTUAL_HOST=*.example.com`

### VIRTUAL_PORT
- **Purpose**: Specifies which port to proxy to when container exposes multiple ports
- **Default**: Port 80
- **Example**: `VIRTUAL_PORT=3000`

### VIRTUAL_PATH
- **Purpose**: Overrides the default nginx location path
- **Default**: `/`
- **Example**: `VIRTUAL_PATH=/api/`

### VIRTUAL_PROTO
- **Purpose**: Use HTTPS for backend connections
- **Default**: `http`
- **Example**: `VIRTUAL_PROTO=https`

### CERT_NAME
- **Purpose**: Specify certificate name for SNI
- **Example**: `CERT_NAME=shared`

## SSL Support

nginx-proxy supports SSL with automatic certificate detection:

```bash
docker run -d -p 80:80 -p 443:443 \
    -v /path/to/certs:/etc/nginx/certs \
    -v /var/run/docker.sock:/tmp/docker.sock:ro \
    nginxproxy/nginx-proxy
```

### Certificate Naming Conventions

- **Single host**: `example.com.crt` and `example.com.key`
- **Wildcard**: `example.com.crt` and `example.com.key` (for `*.example.com`)
- **SNI**: `shared.crt` and `shared.key` with `CERT_NAME=shared`
- **CA Certificate**: `example.com.ca`
- **Diffie-Hellman**: `example.com.dhparam.pem`

### SSL Behavior

- Port 80 redirects to 443 when certificate is available
- Returns 503 when no certificate is available for HTTPS requests
- Supports HSTS and SSL session caching
- Uses Mozilla intermediate SSL profile

## Load Balancing

nginx-proxy automatically load balances across multiple containers with the same `VIRTUAL_HOST`:

```bash
# Start multiple containers with same VIRTUAL_HOST
docker run -d --name app1 -e VIRTUAL_HOST=example.com my-app
docker run -d --name app2 -e VIRTUAL_HOST=example.com my-app
docker run -d --name app3 -e VIRTUAL_HOST=example.com my-app
```

This creates an upstream block with all three containers.

## Advanced Configuration

### Custom Nginx Configuration

#### Proxy-wide Configuration
Place configuration files in `/etc/nginx/conf.d/` with `.conf` extension:

```bash
docker run -d -p 80:80 \
    -v /path/to/my_proxy.conf:/etc/nginx/conf.d/my_proxy.conf:ro \
    -v /var/run/docker.sock:/tmp/docker.sock:ro \
    nginxproxy/nginx-proxy
```

#### Per-VIRTUAL_HOST Configuration
Place configuration files in `/etc/nginx/vhost.d/` named after the virtual host:

```bash
docker run -d -p 80:80 \
    -v /path/to/vhost.d:/etc/nginx/vhost.d:ro \
    -v /var/run/docker.sock:/tmp/docker.sock:ro \
    nginxproxy/nginx-proxy

# Create custom config for specific host
echo 'client_max_body_size 100m;' > /path/to/vhost.d/example.com
```

### Basic Authentication

Create htpasswd files for virtual hosts:

```bash
docker run -d -p 80:80 -p 443:443 \
    -v /path/to/htpasswd:/etc/nginx/htpasswd \
    -v /var/run/docker.sock:/tmp/docker.sock:ro \
    nginxproxy/nginx-proxy

# Create auth file for virtual host
htpasswd -c /path/to/htpasswd/example.com username
```

## Docker Compose Example

```yaml
version: '3'
services:
  nginx-proxy:
    image: nginxproxy/nginx-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/tmp/docker.sock:ro
      - ./certs:/etc/nginx/certs:ro
      - ./vhost.d:/etc/nginx/vhost.d:ro
      - ./htpasswd:/etc/nginx/htpasswd:ro

  web1:
    image: nginx
    environment:
      - VIRTUAL_HOST=example.com
    expose:
      - "80"

  web2:
    image: nginx
    environment:
      - VIRTUAL_HOST=api.example.com
      - VIRTUAL_PATH=/api/
    expose:
      - "80"

  app:
    image: my-app
    environment:
      - VIRTUAL_HOST=app.example.com
      - VIRTUAL_PORT=3000
      - VIRTUAL_PROTO=https
    expose:
      - "3000"
```

## Separate Container Setup

Run nginx-proxy as separate nginx and docker-gen containers:

```bash
# Start nginx
docker run -d -p 80:80 --name nginx \
    -v /tmp/nginx:/etc/nginx/conf.d \
    nginx

# Start docker-gen
docker run --volumes-from nginx \
    -v /var/run/docker.sock:/tmp/docker.sock:ro \
    -v $(pwd):/etc/docker-gen/templates \
    -t nginxproxy/docker-gen \
    -notify-sighup nginx -watch -only-exposed \
    /etc/docker-gen/templates/nginx.tmpl \
    /etc/nginx/conf.d/default.conf
```

## Requirements for Proxied Containers

Containers being proxied must:

1. **Expose ports**: Use `EXPOSE` in Dockerfile or `--expose` flag
2. **Share network**: Be on same Docker network as nginx-proxy
3. **Set VIRTUAL_HOST**: Environment variable for routing

## Template System

nginx-proxy uses Go templates to generate nginx configuration:

```go
{{ range $host, $containers := groupBy $ "Env.VIRTUAL_HOST" }}
upstream {{ $host }} {
{{ range $index, $value := $containers }}
    {{ with $address := index $value.Addresses 0 }}
    server {{ $address.IP }}:{{ $address.Port }};
    {{ end }}
{{ end }}
}

server {
    server_name {{ $host }};
    location / {
        proxy_pass http://{{ $host }};
        include /etc/nginx/proxy_params;
    }
}
{{ end }}
```

## Image Variants

- **Debian-based**: `nginxproxy/nginx-proxy:1.7`
- **Alpine-based**: `nginxproxy/nginx-proxy:1.7-alpine`

⚠️ **Warning**: Avoid using `latest` or `alpine` tags in production.

## Integration with ACME Companion

For automatic SSL certificate generation with Let's Encrypt:

```yaml
version: '3'
services:
  nginx-proxy:
    image: nginxproxy/nginx-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - conf:/etc/nginx/conf.d
      - vhost:/etc/nginx/vhost.d
      - html:/usr/share/nginx/html
      - certs:/etc/nginx/certs:ro
      - /var/run/docker.sock:/tmp/docker.sock:ro

  acme-companion:
    image: nginxproxy/acme-companion
    volumes_from:
      - nginx-proxy
    volumes:
      - certs:/etc/nginx/certs:rw
      - acme:/etc/acme.sh
      - /var/run/docker.sock:/var/run/docker.sock:ro

  web:
    image: nginx
    environment:
      - VIRTUAL_HOST=example.com
      - LETSENCRYPT_HOST=example.com
      - LETSENCRYPT_EMAIL=admin@example.com

volumes:
  conf:
  vhost:
  html:
  certs:
  acme:
```

## Common Use Cases

1. **Development Environment**: Easy local development with custom domains
2. **Microservices**: Route different services by subdomain
3. **Blue-Green Deployments**: Zero-downtime deployments
4. **Multi-tenant Applications**: Host isolation by domain
5. **API Gateway**: Route API endpoints to different services

## Troubleshooting

### Container Not Accessible
- Check if container exposes the correct port
- Verify containers are on the same network
- Check VIRTUAL_HOST environment variable

### SSL Issues
- Verify certificate file naming
- Check certificate file permissions
- Ensure both .crt and .key files exist

### Load Balancing Not Working
- Confirm multiple containers have identical VIRTUAL_HOST
- Check container health status
- Verify all containers expose the same port 