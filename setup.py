"""Setup script for IRA Workflow Builder"""
from setuptools import setup, find_packages

setup(
    name="ira-workflow-builder",
    version="4.0.0",
    packages=find_packages(where="."),
    package_dir={"": "."},
    include_package_data=True,
)
