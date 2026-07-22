from setuptools import setup, find_packages

setup(
    name="robot-cli",
    version="0.1.0",
    description="Robot Development Platform CLI",
    author="Robot Team",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "pyyaml",
    ],
    entry_points={
        "console_scripts": [
            "robot = robot.cli:cli",
        ],
    },
    python_requires=">=3.8",
)