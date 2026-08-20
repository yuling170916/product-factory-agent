"""Compatibility metadata for older setuptools versions.

Modern installers read pyproject.toml. macOS system Python can ship an older
setuptools that ignores PEP 621 metadata, so this small fallback keeps local
editable installs and offline wheel builds usable.
"""

from setuptools import find_packages, setup


setup(
    name="product-factory-agent",
    version="0.1.0",
    description="A gated PRD-to-production workflow agent",
    packages=find_packages("src"),
    package_dir={"": "src"},
    package_data={"product_factory": ["templates/manuals/*.md", "templates/specs/*.md"]},
    include_package_data=True,
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "product-factory=product_factory.cli:main",
            "pf=product_factory.cli:main",
        ]
    },
)
