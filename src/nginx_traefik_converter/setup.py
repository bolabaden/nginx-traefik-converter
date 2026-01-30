from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

setup(
    name="nginx-traefik-converter",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Universal nginx/Traefik configuration converter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/nginx-traefik-converter",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: System :: Systems Administration",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "nginx-traefik-converter=nginx_traefik_converter.split_docker_compose_yaml:cli",
            "ntc=nginx_traefik_converter.split_docker_compose_yaml:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
