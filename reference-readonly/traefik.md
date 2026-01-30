# Traefik Documentation

Traefik is a modern reverse proxy and load balancer that makes deploying microservices easy. It automatically discovers services and configures itself dynamically.

## Overview

Traefik is designed to be a cloud-native application proxy that integrates with existing infrastructure components and configures itself automatically and dynamically.

### Key Features

- **Automatic Service Discovery**: Automatically discovers services in your infrastructure
- **Dynamic Configuration**: Configuration updates with zero downtime
- **Multiple Protocols**: HTTP, HTTPS, TCP, UDP support
- **Load Balancing**: Multiple load balancing algorithms
- **SSL/TLS Termination**: Automatic SSL certificate management with Let's Encrypt
- **Middleware Support**: Request/response transformation and authentication
- **Observability**: Metrics, tracing, and access logs

## Core Concepts

### Routers
Routers are in charge of connecting incoming requests to the services that can handle them.

#### HTTP Routers
HTTP routers analyze requests (host, path, headers, etc.) to determine which service should handle them.

**Configuration Example:**
```yaml
http:
  routers:
    my-router:
      rule: "Host(`example.com`)"
      service: my-service
```

#### TCP Routers
TCP routers handle TCP connections and can route based on SNI (Server Name Indication).

**Configuration Example:**
```yaml
tcp:
  routers:
    my-tcp-router:
      rule: "HostSNI(`example.com`)"
      service: my-tcp-service
      tls: {}
```

#### UDP Routers
UDP routers handle UDP packets and act primarily as load balancers.

**Configuration Example:**
```yaml
udp:
  routers:
    my-udp-router:
      service: my-udp-service
      entryPoints:
        - "udp-port"
```

### Rules and Matchers

Traefik uses rules to match incoming requests. Rules are composed of matchers.

#### HTTP Matchers

| Matcher | Description | Example |
|---------|-------------|---------|
| `Host()` | Match request host | `Host('example.com')` |
| `HostRegexp()` | Match host with regex | `HostRegexp('[a-z]+\.example\.com')` |
| `Path()` | Match exact path | `Path('/api')` |
| `PathPrefix()` | Match path prefix | `PathPrefix('/api/')` |
| `PathRegexp()` | Match path with regex | `PathRegexp('\.jpg$')` |
| `Method()` | Match HTTP method | `Method('GET')` |
| `Header()` | Match header value | `Header('Content-Type', 'application/json')` |
| `HeaderRegexp()` | Match header with regex | `HeaderRegexp('Content-Type', '^application/(json\|yaml)$')` |
| `Query()` | Match query parameter | `Query('mobile', 'true')` |
| `QueryRegexp()` | Match query with regex | `QueryRegexp('mobile', '^(true\|yes)$')` |
| `ClientIP()` | Match client IP | `ClientIP('192.168.1.0/24')` |

#### TCP Matchers

| Matcher | Description | Example |
|---------|-------------|---------|
| `HostSNI()` | Match SNI hostname | `HostSNI('example.com')` |
| `HostSNIRegexp()` | Match SNI with regex | `HostSNIRegexp('^.+\.example\.com$')` |
| `ClientIP()` | Match client IP | `ClientIP('192.168.1.0/24')` |
| `ALPN()` | Match ALPN protocol | `ALPN('h2')` |

#### Complex Rules

Rules can be combined using logical operators:

```yaml
# AND operator
rule: "Host(`example.com`) && Path(`/api`)"

# OR operator  
rule: "Host(`example.com`) || Host(`example.org`)"

# NOT operator
rule: "Host(`example.com`) && !Path(`/admin`)"

# Parentheses for grouping
rule: "Host(`example.com`) || (Host(`example.org`) && Path(`/api`))"
```

### Services

Services define how to reach the actual services that will handle the requests.

#### HTTP Services

```yaml
http:
  services:
    my-service:
      loadBalancer:
        servers:
          - url: "http://192.168.1.10:8080"
          - url: "http://192.168.1.11:8080"
```

#### TCP Services

```yaml
tcp:
  services:
    my-tcp-service:
      loadBalancer:
        servers:
          - address: "192.168.1.10:3306"
          - address: "192.168.1.11:3306"
```

#### UDP Services

```yaml
udp:
  services:
    my-udp-service:
      loadBalancer:
        servers:
          - address: "192.168.1.10:53"
          - address: "192.168.1.11:53"
```

### EntryPoints

EntryPoints define the ports on which Traefik listens for incoming connections.

```yaml
entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"
  mysql:
    address: ":3306"
  dns:
    address: ":53/udp"
```

### Middlewares

Middlewares allow you to modify requests and responses.

#### HTTP Middlewares

- **AddPrefix**: Add a path prefix
- **BasicAuth**: Basic authentication
- **Buffering**: Request/response buffering
- **Chain**: Chain multiple middlewares
- **CircuitBreaker**: Circuit breaker pattern
- **Compress**: Response compression
- **DigestAuth**: Digest authentication
- **Errors**: Custom error pages
- **ForwardAuth**: Forward authentication
- **Headers**: Modify headers
- **IPAllowList**: IP allowlist
- **InFlightReq**: Limit concurrent requests
- **PassTLSClientCert**: Pass client certificates
- **RateLimit**: Rate limiting
- **RedirectRegex**: Regex-based redirects
- **RedirectScheme**: Scheme redirects
- **ReplacePath**: Replace request path
- **ReplacePathRegex**: Regex path replacement
- **Retry**: Request retry logic
- **StripPrefix**: Remove path prefix
- **StripPrefixRegex**: Regex prefix removal

#### TCP Middlewares

- **InFlightConn**: Limit concurrent connections
- **IPAllowList**: IP allowlist

### TLS Configuration

Traefik supports comprehensive TLS configuration:

#### Automatic Certificate Management

```yaml
http:
  routers:
    my-router:
      rule: "Host(`example.com`)"
      service: my-service
      tls:
        certResolver: letsencrypt
```

#### Manual Certificate Configuration

```yaml
http:
  routers:
    my-router:
      rule: "Host(`example.com`)"
      service: my-service
      tls:
        options: default

tls:
  options:
    default:
      minVersion: VersionTLS12
      cipherSuites:
        - TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
        - TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256
```

## Provider Configuration

### Docker Provider

Traefik can automatically discover services from Docker containers using labels:

```yaml
# docker-compose.yml
services:
  whoami:
    image: traefik/whoami
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.whoami.rule=Host(`whoami.example.com`)"
      - "traefik.http.routers.whoami.entrypoints=websecure"
      - "traefik.http.routers.whoami.tls.certresolver=letsencrypt"
      - "traefik.http.services.whoami.loadbalancer.server.port=80"
```

### File Provider

Static configuration in files:

```yaml
# traefik.yml
api:
  dashboard: true

entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"

providers:
  file:
    filename: dynamic.yml
    watch: true

certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@example.com
      storage: acme.json
      httpChallenge:
        entryPoint: web
```

### Kubernetes Provider

Traefik integrates with Kubernetes using:

1. **Ingress**: Standard Kubernetes Ingress resources
2. **IngressRoute**: Traefik's Custom Resource Definition (CRD)
3. **Gateway API**: Kubernetes Gateway API support

#### IngressRoute Example

```yaml
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: my-app
spec:
  entryPoints:
    - websecure
  routes:
    - match: Host(`my-app.example.com`)
      kind: Rule
      services:
        - name: my-app-service
          port: 80
  tls:
    certResolver: letsencrypt
```

## Priority and Routing

### Priority Calculation

Routes are sorted by default in descending order using rule length. Longer rules have higher priority.

```yaml
http:
  routers:
    specific-router:
      rule: "Host(`api.example.com`) && Path(`/v1/users`)"
      priority: 100
      service: users-service
    
    general-router:
      rule: "Host(`api.example.com`)"
      priority: 1
      service: api-service
```

### Rule Syntax

Traefik v3 introduced a new rule syntax. The `ruleSyntax` option allows per-router syntax configuration:

```yaml
http:
  routers:
    v3-router:
      rule: "HostRegexp(`[a-z]+\\.example\\.com`)"
      ruleSyntax: v3
    
    v2-router:
      rule: "HostRegexp(`{subdomain:[a-z]+}.example.com`)"
      ruleSyntax: v2
```

## Load Balancing

Traefik supports multiple load balancing algorithms:

### Algorithms

- **Round Robin** (default): Requests are distributed evenly
- **Weighted Round Robin**: Servers have different weights
- **Least Connections**: Route to server with fewest active connections
- **Weighted Least Connections**: Combines weights with connection count
- **Random**: Random server selection
- **Weighted Random**: Random selection with weights

```yaml
http:
  services:
    my-service:
      loadBalancer:
        servers:
          - url: "http://192.168.1.10:8080"
            weight: 3
          - url: "http://192.168.1.11:8080"
            weight: 1
        healthCheck:
          path: /health
          interval: 30s
          timeout: 5s
```

## Observability

### Metrics

Traefik supports multiple metrics backends:

- **Prometheus**: For monitoring and alerting
- **DataDog**: APM and infrastructure monitoring
- **StatsD**: Metrics aggregation
- **InfluxDB**: Time series database
- **OpenTelemetry**: Vendor-neutral observability

```yaml
metrics:
  prometheus:
    addEntryPointsLabels: true
    addServicesLabels: true
    addRoutersLabels: true
```

### Tracing

Distributed tracing support:

- **Jaeger**: End-to-end distributed tracing
- **Zipkin**: Distributed tracing system
- **OpenTelemetry**: Vendor-neutral tracing
- **DataDog**: APM tracing

```yaml
tracing:
  jaeger:
    samplingServerURL: http://jaeger:14268/api/sampling
    localAgentHostPort: jaeger:6831
```

### Access Logs

Detailed request logging:

```yaml
accessLog:
  filePath: "/var/log/traefik/access.log"
  format: json
  fields:
    headers:
      defaultMode: keep
      names:
        Authorization: drop
```

## Security Features

### TLS Options

```yaml
tls:
  options:
    secure:
      minVersion: VersionTLS13
      cipherSuites:
        - TLS_AES_256_GCM_SHA384
        - TLS_CHACHA20_POLY1305_SHA256
      sniStrict: true
```

### HTTPS Redirect

```yaml
http:
  middlewares:
    https-redirect:
      redirectScheme:
        scheme: https
        permanent: true
```

### Rate Limiting

```yaml
http:
  middlewares:
    rate-limit:
      rateLimit:
        burst: 100
        average: 50
```

### IP Filtering

```yaml
http:
  middlewares:
    ip-allowlist:
      ipAllowList:
        sourceRange:
          - "192.168.1.0/24"
          - "10.0.0.0/8"
```

## Configuration Examples

### Complete Docker Compose Setup

```yaml
version: '3.8'

services:
  traefik:
    image: traefik:v3.0
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./letsencrypt:/letsencrypt"
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.dashboard.rule=Host(`traefik.example.com`)"
      - "traefik.http.routers.dashboard.tls.certresolver=letsencrypt"
      - "traefik.http.routers.dashboard.service=api@internal"

  app:
    image: nginx
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.app.rule=Host(`app.example.com`)"
      - "traefik.http.routers.app.entrypoints=websecure"
      - "traefik.http.routers.app.tls.certresolver=letsencrypt"
      - "traefik.http.services.app.loadbalancer.server.port=80"
```

### File-based Configuration

**Static Configuration (traefik.yml):**
```yaml
api:
  dashboard: true

entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"

providers:
  file:
    filename: dynamic.yml
    watch: true

certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@example.com
      storage: acme.json
      httpChallenge:
        entryPoint: web
```

**Dynamic Configuration (dynamic.yml):**
```yaml
http:
  routers:
    api:
      rule: "Host(`api.example.com`)"
      service: api-service
      tls:
        certResolver: letsencrypt
      middlewares:
        - auth

  middlewares:
    auth:
      basicAuth:
        users:
          - "admin:$2y$10$..."

  services:
    api-service:
      loadBalancer:
        servers:
          - url: "http://192.168.1.10:8080"
          - url: "http://192.168.1.11:8080"
        healthCheck:
          path: /health
          interval: 30s

tls:
  options:
    default:
      minVersion: VersionTLS12
```

## Migration and Compatibility

### Traefik v2 to v3 Migration

Key changes in v3:
- New rule syntax (backward compatible with `ruleSyntax` option)
- Updated middleware configurations
- Enhanced observability features
- Improved Kubernetes integration

### Best Practices

1. **Use specific rules**: More specific rules should have higher priority
2. **Health checks**: Always configure health checks for services
3. **TLS security**: Use modern TLS versions and cipher suites
4. **Monitoring**: Enable metrics and tracing for production
5. **Rate limiting**: Implement rate limiting for public-facing services
6. **IP filtering**: Use IP allowlists for sensitive endpoints
7. **Certificate management**: Use automated certificate renewal
8. **Resource limits**: Configure appropriate resource limits for containers

## Troubleshooting

### Common Issues

1. **Route conflicts**: Check rule priorities and specificity
2. **Certificate issues**: Verify ACME challenge configuration
3. **Service discovery**: Ensure proper labels/annotations
4. **Load balancing**: Check health check configuration
5. **TLS errors**: Verify certificate and TLS options
6. **Performance**: Monitor metrics and adjust configuration

### Debugging Tools

- **Dashboard**: Visual interface for configuration inspection
- **API**: Programmatic access to configuration and metrics
- **Logs**: Detailed logging for troubleshooting
- **Ping**: Health check endpoint
- **Metrics**: Performance and health monitoring 