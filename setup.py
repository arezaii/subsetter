import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="parflow_subsetter",
    version="0.0.17",
    author="Ahmad Rezaii",
    author_email="ahmadrezaii@u.boisestate.edu",
    description="A set of tools for clipping ParFlow models and their outputs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arezaii/subsetter",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_pionts={
        "console_scripts": [
            "subset_conus = parflow.subset.tools.subset_conus:main",
            "rasterize_shape = parflow.subset.tools.rasterize_shape:main",
            "bulk_clip = parflow.subset.tools.bulk_clip:main",
        ]
    },
    python_requires='>=3.6',
    install_requires=['pyyaml>=5.3.0', 'pandas>=1.0', 'gdal==2.2.2', 'parflowio'],
    namespace_packages=['parflow'],
)