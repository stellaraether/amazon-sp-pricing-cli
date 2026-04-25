from setuptools import find_packages, setup

setup(
    name="amazon-sp-cli",
    version="0.1.2",
    description="CLI tool for Amazon Selling Partner API (SP-API) operations",
    author="Lunan Li",
    author_email="lunan@stellaraether.com",
    url="https://github.com/stellaraether/amazon-sp-cli",
    packages=find_packages(),
    install_requires=[
        "click>=8.0",
        "requests>=2.27.0",
        "boto3>=1.20.0",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "amz-sp=amazon_sp_cli.main:cli",
        ],
    },
    data_files=[
        ("share/amazon-sp-cli", ["README.md"]),
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
