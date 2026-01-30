# Universal nginx/Traefik Configuration Converter

A comprehensive tool for converting between nginx and Traefik configurations, supporting multiple input/output formats and bidirectional conversion. Similar to Kubernetes' Kompose tool but for reverse proxy configurations.

## Features

### 🔄 **Bidirectional Conversion**

- nginx.conf ↔ Traefik dynamic configuration
- docker-compose labels ↔ standalone configurations  
- JSON/YAML ↔ native config formats

### 📋 **Supported Input Formats**

- Docker Compose files with Traefik labels
- Traefik dynamic configuration (YAML/JSON)
- Traefik static configuration
- nginx.conf files
- nginx-proxy environment variables
- Raw JSON/YAML configurations

### 📤 **Supported Output Formats**

- Traefik dynamic configuration
- nginx.conf with upstream blocks
- Docker Compose with labels
- JSON/YAML for further processing

### 🎯 **Advanced Features**

- **Full Traefik v3 syntax support** - All matchers (Host, Path, Method, Header, Query, ClientIP, etc.)
- **Complex rule parsing** - Logical operators (&&, ||, !), parentheses, precedence
- **TCP/UDP routing** - Support for non-HTTP protocols
- **Middleware conversion** - Authentication, rate limiting, headers
- **TLS configuration** - Certificate management and SSL termination
- **Load balancing** - Multiple backend servers and health checks
- **Configuration validation** - Syntax checking and best practice warnings
- **Rich CLI interface** - Progress bars, colored output, interactive prompts

## Installation

### From PyPI (when published)

```bash
pip install nginx-traefik-converter
```

### From Source

```bash
git clone https://github.com/yourusername/nginx-traefik-converter.git
cd nginx-traefik-converter
pip install -e .
```

### Dependencies

```bash
pip install -r requirements.txt
```

## Quick Start

### Convert Docker Compose to Traefik Dynamic Config

```bash
# Auto-detect input format
ntc convert docker-compose.yml traefik-dynamic.yml --output-format traefik-dynamic

# Explicit format specification
ntc convert docker-compose.yml traefik.yml -i docker-compose -o traefik-dynamic
```

### Convert Traefik to nginx

```bash
ntc convert traefik-dynamic.yml nginx.conf --output-format nginx-conf
```

### Analyze Configuration

```bash
ntc analyze docker-compose.yml
ntc analyze traefik-dynamic.yml --format traefik-dynamic
```

### Generate Complete Setup

```bash
# Generate docker-compose + configs + documentation
ntc scaffold config.yml --output-dir ./proxy-setup --proxy-type traefik --include-compose --include-config --include-docs
```

## Usage Examples

### Basic Conversion

```bash
# Convert docker-compose to Traefik
ntc convert docker-compose.novpn.yml traefik-dynamic.yml -o traefik-dynamic

# Convert Traefik to nginx
ntc convert traefik-dynamic.yml nginx.conf -o nginx-conf

# Dry run to preview output
ntc convert docker-compose.yml output.yml -o traefik-dynamic --dry-run
```

### Advanced Analysis

```bash
# Detailed configuration analysis
ntc analyze docker-compose.yml

# Validate without conversion
ntc convert input.yml output.yml -o traefik-dynamic --validate --dry-run
```

### Scaffolding Projects

```bash
# Create complete Traefik setup
ntc scaffold docker-compose.yml -o ./traefik-setup -p traefik --include-all

# Create nginx setup with documentation
ntc scaffold config.yml -o ./nginx-setup -p nginx --include-config --include-docs
```

## Configuration Examples

### Input: Docker Compose with Traefik Labels

```yaml
services:
  web:
    image: nginx
    labels:
      traefik.enable: "true"
      traefik.http.routers.web.rule: "Host(`example.com`) && PathPrefix(`/api`)"
      traefik.http.routers.web.middlewares: "auth,rate-limit"
      traefik.http.routers.web.tls: "true"
      traefik.http.services.web.loadbalancer.server.port: "80"
```

### Output: Traefik Dynamic Configuration

```yaml
http:
  routers:
    web:
      rule: "Host(`example.com`) && PathPrefix(`/api`)"
      service: web
      middlewares:
        - auth
        - rate-limit
      tls: {}
  services:
    web:
      loadBalancer:
        servers:
          - url: "http://web:80"
```

### Output: nginx.conf

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;
    
    ssl_certificate /etc/nginx/ssl/web.crt;
    ssl_certificate_key /etc/nginx/ssl/web.key;
    
    location /api {
        proxy_pass http://web:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Supported Traefik Features

### HTTP Matchers

- ✅ `Host()` - Exact hostname matching
- ✅ `HostRegexp()` - Regex hostname matching  
- ✅ `Path()` - Exact path matching
- ✅ `PathPrefix()` - Path prefix matching
- ✅ `PathRegexp()` - Regex path matching
- ✅ `Method()` - HTTP method matching
- ✅ `Header()` - Header value matching
- ✅ `HeaderRegexp()` - Regex header matching
- ✅ `Query()` - Query parameter matching
- ✅ `QueryRegexp()` - Regex query matching
- ✅ `ClientIP()` - Client IP matching

### TCP/UDP Matchers

- ✅ `HostSNI()` - SNI hostname matching
- ✅ `HostSNIRegexp()` - Regex SNI matching
- ✅ `ClientIP()` - Client IP for TCP/UDP
- ✅ `ALPN()` - ALPN protocol matching

### Advanced Features

- ✅ Logical operators (`&&`, `||`, `!`)
- ✅ Parentheses and precedence
- ✅ Multiple routers per service
- ✅ Middleware chains
- ✅ TLS termination
- ✅ Load balancer configuration
- ✅ Health checks
- ✅ Priority-based routing

## CLI Commands

### `convert`

Convert between configuration formats.

```bash
ntc convert INPUT OUTPUT [OPTIONS]

Options:
  -i, --input-format [docker-compose|traefik-dynamic|nginx-conf|json|yaml]
  -o, --output-format [traefik-dynamic|nginx-conf|docker-compose|json|yaml]
  --validate / --no-validate    Validate configuration (default: true)
  --dry-run                     Preview output without writing files
```

### `analyze`

Analyze and display configuration details.

```bash
ntc analyze CONFIG_FILE [OPTIONS]

Options:
  -f, --format [docker-compose|traefik-dynamic|nginx-conf|json|yaml]
```

### `scaffold`

Generate complete proxy setup with configs and documentation.

```bash
ntc scaffold INPUT [OPTIONS]

Options:
  -o, --output-dir PATH         Output directory
  -p, --proxy-type [traefik|nginx]  Target proxy type
  --include-compose             Generate docker-compose.yml
  --include-config              Generate proxy configuration
  --include-docs                Generate documentation
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/yourusername/nginx-traefik-converter.git
cd nginx-traefik-converter
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
pip install -r requirements-dev.txt
```

### Run Tests

```bash
pytest tests/
pytest tests/ --cov=src/nginx_traefik_converter
```

### Code Quality

```bash
black src/ tests/
isort src/ tests/
flake8 src/ tests/
mypy src/
```

## Architecture

### Core Components

1. **ConfigParser** - Universal configuration parser supporting multiple formats
2. **TraefikRuleParser** - Advanced Traefik rule syntax parser with full v3 support
3. **ConfigGenerator** - Multi-format configuration generator with Jinja2 templates
4. **ConfigValidator** - Configuration validation and best practice checking
5. **Route/Service Models** - Unified data models for cross-format compatibility

### Data Flow

```
Input Config → Parser → Unified Model → Validator → Generator → Output Config
```

### Supported Conversions Matrix

| From / To | docker-compose | traefik-dynamic | nginx-conf | JSON/YAML |
|-----------|----------------|-----------------|------------|-----------|
| docker-compose | ➖ | ✅ | ✅ | ✅ |
| traefik-dynamic | ✅ | ➖ | ✅ | ✅ |  
| nginx-conf | ✅ | ✅ | ➖ | ✅ |
| JSON/YAML | ✅ | ✅ | ✅ | ➖ |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Adding New Features

- New input/output formats: Extend `ConfigParser` and `ConfigGenerator`
- New matchers: Update `TraefikRuleParser.MATCHERS`
- New CLI commands: Add to the Click command group

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by [Kompose](https://kompose.io/) for Kubernetes
- Built with [Click](https://click.palletsprojects.com/) for CLI
- Uses [Rich](https://rich.readthedocs.io/) for beautiful terminal output
- Template engine powered by [Jinja2](https://jinja.palletsprojects.com/)

## Roadmap

- [ ] GUI web interface
- [ ] Kubernetes Ingress support  
- [ ] HAProxy configuration support
- [ ] Configuration migration tools
- [ ] Performance benchmarking
- [ ] Plugin system for custom formats
- [ ] Real-time configuration validation
- [ ] Integration with CI/CD pipelines
