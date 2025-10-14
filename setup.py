from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in lt_piece_rate_pay_report/__init__.py
from lt_piece_rate_pay_report import __version__ as version

setup(
	name="lt_piece_rate_pay_report",
	version=version,
	description="Reports of Lt piece Rate ay",
	author="LTL",
	author_email="ltl@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
