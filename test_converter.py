#!/usr/bin/env python3
"""
Simple test script for the nginx/Traefik converter
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nginx_traefik_converter.core.converter import UniversalConverter
from nginx_traefik_converter.models.config import ProxyConfig, Route, Service


def test_basic_conversion():
    """Test basic conversion functionality"""
    print("Testing basic conversion functionality...")

    # Create a simple test configuration
    config = ProxyConfig()

    # Add a test route
    route = Route(
        name="test-router",
        host="example.com",
        path_prefix="/api",
        service="web-service",
        tls=True,
    )
    config.add_route(route)

    # Add a test service
    service = Service(name="web-service", servers=["web:80"], port=80)
    config.add_service(service)

    # Test conversion
    converter = UniversalConverter()

    try:
        # Test nginx generation
        nginx_config = converter.generate_config(config, "nginx-conf")
        print("✓ Nginx configuration generated successfully")
        print(f"Generated config length: {len(nginx_config)} characters")

        # Test Traefik generation
        traefik_config = converter.generate_config(config, "traefik-dynamic")
        print("✓ Traefik configuration generated successfully")
        print(f"Generated config length: {len(traefik_config)} characters")

        # Test Docker Compose generation
        compose_config = converter.generate_config(config, "docker-compose")
        print("✓ Docker Compose configuration generated successfully")
        print(f"Generated config length: {len(compose_config)} characters")

        print("\n🎉 All tests passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_parsers():
    """Test parser functionality"""
    print("\nTesting parser functionality...")

    # Create a simple test docker-compose content
    test_compose = """
version: '3.8'
services:
  web:
    image: nginx
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.web.rule=Host(`example.com`) && PathPrefix(`/api`)"
      - "traefik.http.services.web.loadbalancer.server.port=80"
    ports:
      - "8080:80"
"""

    # Write test file
    test_file = Path("test-docker-compose.yml")
    test_file.write_text(test_compose)

    try:
        converter = UniversalConverter()
        config = converter.parse_config(test_file, "docker-compose")

        print(f"✓ Parsed {len(config.routes)} routes")
        print(f"✓ Parsed {len(config.services)} services")

        # Clean up
        test_file.unlink()

        print("✓ Parser test passed!")
        return True

    except Exception as e:
        print(f"❌ Parser test failed: {e}")
        if test_file.exists():
            test_file.unlink()
        return False


if __name__ == "__main__":
    print("🧪 Testing nginx/Traefik Converter")
    print("=" * 50)

    success = True

    # Run tests
    success &= test_basic_conversion()
    success &= test_parsers()

    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! The converter is working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)
 