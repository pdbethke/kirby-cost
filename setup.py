"""Setup script for kirby-cost, the HERO System 6E build/cost engine."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="kirby-cost",
    version="0.1.40",
    author="Peter D Bethke",
    description="HERO System 6th Edition character build and cost engine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pdbethke/kirby-cost",
    # Exclude tests from the distribution: they are 38 modules of bloat,
    # they make "tests" an importable TOP-LEVEL package that can collide
    # with a consumer's own, and the oracle suite they contain is
    # meaningless without fixtures the wheel deliberately does not ship.
    packages=find_packages(exclude=["tests", "tests.*"]),
    # No package data. The engine ships no Hero Games content of any kind:
    # templates, the language similarity chart and the oracle corpus all come
    # from the user's own licensed HERO Designer installation. A
    # language_chart.json extracted from Main6E.hdt shipped here until
    # 2026-08-17; it is gone, and nothing replaced it.
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        # PolyForm Noncommercial 1.0.0 is source-available, NOT OSI-approved,
        # so no OSI classifier applies. See LICENSE.
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    license="PolyForm-Noncommercial-1.0.0",
    license_files=["LICENSE"],
    python_requires=">=3.10",
    install_requires=[
        "typing-extensions>=4.8.0",
        "lxml>=4.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "mypy>=1.5.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
)

