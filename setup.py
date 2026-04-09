from setuptools import setup, find_packages

setup(
	name="agent_incentives",
	version="0.0.1",
    description="Agent incentive engine scaffold for SRIAAS",
	author="SRIAAS",
    author_email="webdevelopersriaas@gmail.com",
	packages=find_packages(),
	include_package_data=True,
    zip_safe=False,
)