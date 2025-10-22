"""Setup script for IRA Workflow Builder"""
from setuptools import setup, find_packages

setup(
    name="ira-workflow-builder",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    packages=find_packages(where="."),
    package_dir={"": "."},
    include_package_data=True,
)
