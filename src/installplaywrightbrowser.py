from setuptools import setup, find_packages
from setuptools.command.install import install as _install
from playwright.sync_api import sync_playwright

class InstallWithPlaywright(_install):
    def run(self):
        _install.run(self)
        self.install_playwright()

    def install_playwright(self):
        print("Installing Playwright browsers...")
        with sync_playwright() as p:
            p.chromium.install()
        print("Playwright browsers installed.")

setup(
    name="your_project_name",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'playwright',  # Add other dependencies here
    ],
    cmdclass={
        'install': InstallWithPlaywright,
    },
)
