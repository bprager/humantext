from setuptools import find_packages, setup

setup(
    name="humantext",
    version="0.1.0",
    description="Local-first editorial intelligence engine to detect and revise AI-style writing.",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={"console_scripts": ["humantext=humantext.cli.main:main"]},
)
