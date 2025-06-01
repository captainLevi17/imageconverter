from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="image-master",
    version="0.5.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A powerful desktop application for image processing and conversion",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/imageconverter",
    packages=find_packages(),
    package_data={
        "": ["*.ui", "*.qss", "*.png", "*.ico"],
    },
    install_requires=[
        "PyQt5>=5.15.9",
        "Pillow>=10.1.0",
        "opencv-python>=4.9.0.80",
        "rembg>=2.0.50",
        "imageio>=2.34.0",
        "piexif>=1.1.3",
        "pyheif>=0.7.0",
        "pillow-heif>=0.10.0",
        "onnxruntime>=1.15.1,<2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-qt>=4.2.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.1",
            "pytest-xvfb>=2.0.0",
            "black>=23.3.0",
            "flake8>=6.0.0",
            "mypy>=1.3.0",
            "isort>=5.12.0",
            "pre-commit>=3.3.3",
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "myst-parser>=1.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    entry_points={
        "gui_scripts": [
            "image-master=main:main",
        ],
    },
)
