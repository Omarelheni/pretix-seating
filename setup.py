import os
from distutils.command.build import build

from django.core import management
from setuptools import find_packages, setup

from seating_plan import __version__


try:
    with open(
        os.path.join(os.path.dirname(__file__), "README.rst"), encoding="utf-8"
    ) as f:
        long_description = f.read()
except Exception:
    long_description = ""


class CustomBuild(build):
    def run(self):
        management.call_command("compilemessages", verbosity=1)
        build.run(self)


cmdclass = {"build": CustomBuild}


setup(
    name="seating_plan",
    version=__version__,
    description="Ticket buyers can choose their own seats on an interactive seating plan. We can handle every venue from small cinemas or ballrooms up to large-scale stadiums.",
    long_description=long_description,
    url="GitHub repository URL",
    author="Evey",
    author_email="Your email",
    license="Apache",
    install_requires=[],
    packages=find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,
    cmdclass=cmdclass,
    entry_points="""
[pretix.plugin]
seating_plan=seating_plan:PretixPluginMeta
""",
)
