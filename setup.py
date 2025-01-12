from setuptools import setup, find_packages

# 读取requirements.txt文件
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

print(requirements)

setup(
    name="genstyle_common",
    version="0.1.0", 
    packages=find_packages(),
    install_requires=requirements,
    author="Genstyle Team",
    description="Common utilities for Genstyle services",
    python_requires=">=3.8",
)