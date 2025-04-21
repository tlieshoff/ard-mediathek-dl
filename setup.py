from setuptools import setup, find_packages

setup(
    name='ard-mediathek-dl',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'requests',
        'beautifulsoup4'
    ],
    entry_points={
        'console_scripts': [
            'ard-dl=ard_mediathek_dl.cli:main'
        ]
    },
    python_requires='>=3.10',
)
