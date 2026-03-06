from pathlib import Path

from setuptools import find_packages, setup

VERSION = Path("src/humantext/VERSION").read_text(encoding="utf-8").strip()

setup(
    name="humantext",
    version=VERSION,
    description="Local-first editorial intelligence engine to detect and revise AI-style writing.",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={"humantext": ["VERSION"]},
    entry_points={"console_scripts": ["humantext=humantext.cli.main:main"]},
)
