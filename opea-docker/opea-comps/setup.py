from setuptools import setup, find_packages

setup(
    name="opea-comps",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.26.0",
        "pydantic>=1.8.2",
        "fastapi>=0.68.0",
    ],
    author="OPEA Team",
    author_email="info@opea.com",
    description="Microservices components for OPEA - Open Platform for Educational AI",
    long_description="A framework for building and orchestrating AI microservices for educational applications",
    keywords="microservices, llm, ai, education, language-learning",
    url="https://github.com/opea-project/opea-comps",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)