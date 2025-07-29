from setuptools import setup, find_packages

with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="alfred",
    version="0.1.0",
    description="Personal AI Operator System",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "alfred=cli.main:app",
        ],
    },
    python_requires=">=3.10",
)