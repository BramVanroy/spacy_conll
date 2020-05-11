from pathlib import Path
from setuptools import setup

with Path('README.rst').open(encoding='utf-8') as fhin:
    long_description = fhin.read()

setup(
    name='spacy_conll',
    version='2.0.0',
    description='A custom pipeline component for spaCy that can convert any parsed Doc'
                ' and its sentences into CoNLL-U format. Also provides a command line entry point.',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    keywords='nlp spacy spacy-extension conll conllu tagging parsing stanza spacy_stanza udpipe spacy_udpipe',
    packages=['spacy_conll'],
    url='https://github.com/BramVanroy/spacy_conll',
    author='Bram Vanroy',
    author_email='bramvanroy@hotmail.com',
    license='BSD 2',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
        'Topic :: Text Processing',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Operating System :: OS Independent'
    ],
    project_urls={
        'Bug Reports': 'https://github.com/BramVanroy/spacy_conll/issues',
        'Source': 'https://github.com/BramVanroy/spacy_conll',
    },
    python_requires='>=3.6',
    install_requires=[
        'spacy>=2.0',
        'packaging'
    ],
    extras_require={
        "dev":  ["pytest", "flake8", "isort", "black"],
        "pd": ["pandas"]
    },
    entry_points={
        'console_scripts': ['parse-as-conll=spacy_conll.__main__:main']
    }
)
