import setuptools

# Version will be read from version.py
version = ""
name = "src"

# Fetch ReadMe
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Use requirements.txt to set the install_requires
with open("requirements.txt", encoding="utf-8") as f:
    install_requires = [line.strip() for line in f]

setuptools.setup(
    name="FlaskCelery",  # noqa: F821
    version=version,  # noqa: F821
    author="SandyChen",
    author_email="sandy1990418@gmail.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sandy1990418/Flask-Celery-Template",
    packages=setuptools.find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
    ],
)
