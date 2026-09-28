from setuptools import setup, find_packages

setup(
    name="hwscan",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "psutil>=5.9.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "hwscan = hwscan.cli:main",
        ],
    },
)
