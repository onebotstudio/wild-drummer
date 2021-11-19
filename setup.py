
from os import path
from setuptools import setup, find_packages


VERSION = '0.1.0'
DESCRIPTION = 'Turn sound samples into drums.'
ROOT_DIR = path.dirname(path.abspath(__file__))

with open(path.join(ROOT_DIR, 'requirements.txt')) as f:
    required = f.read().splitlines()

setup(
    name = 'wilddrummer',
    version = VERSION,
    description = DESCRIPTION,
    url = 'https://github.com/onebotstudio/wild-drummer',
    author = 'OneBotStudio',
    packages = find_packages(include = ['wilddrummer', 'wilddrummer.*']),
    entry_points = {
        'console_scripts': [
            'wilddrummer = wilddrummer.wild_drummer:main',
        ],
    },
    install_requires = required,
    extras_require = {
        'interactive': ['matplotlib'],
    },
    python_requires=">=3.7",
)
