# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

# To publish :
# python3 -m pip install --upgrade build twine
# python3 -m build
# python3 -m twine upload --repository pypi dist/*

#  make wheel:
# python setup.py bdist_wheel

setup(
    name="scivianna",
    version="0.1.0",
    description="Visualize Tripoli 4/5 and Apollo3 geometries.",
    author="CEA",
    maintainer="Thibault Moulignier",
    author_email="Thibault.Moulignier@cea.fr",
    package_dir={"": "src"},  # Optional
    packages=find_packages(where="src"),  # Required
    package_data={
        "scivianna": [
            "components/*.py",
            "default_jdd/*",
            "interface/*.py",
            "layout/*.py",
            "panel/*.py",
            "plotter_1d/*.py",
            "plotter_2d/*.py",
            "utils/*.py",
            "*.sh",
        ]
    },
    keywords="visualization",
    python_requires=">=3.8, <4",
    install_requires=[
        "panel",
        "rasterio",
        "matplotlib",
        "numpy<2",
        "shapely",
        "jupyter_bokeh",
        "holoviews",
        "icoco~=2.0.0",
        "panel_material_ui",
        "geopandas"
    ],
    extras_require={
        # 'docs-requirements-txt': [
        #     'sphinx',
        #     'sphinx_rtd_theme',
        # ]
    },
)
