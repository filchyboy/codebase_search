from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="code-search-cli",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A CLI tool for searching through codebases",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/code-search-cli",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click",
        "pyyaml",
        "python-dotenv",
        "rich",
        "loguru",
    ],
    entry_points={
        "console_scripts": [
            "code-search=cli.search_cli:cli",
        ],
    },
)
