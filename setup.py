from setuptools import setup

setup(
    name='spacy_conll',
    version='0.0.2',
    description='Parses a given input text into CoNLL-U format by transforming spaCy output.',
    keywords='nlp spacy conll conllu tagging',
    packages=['spacy_conll'],
    url='https://github.com/BramVanroy/spacy_conll',
    author='Bram Vanroy, Raquel G. Alhama',
    author_email='bramvanroy@hotmail.com, rgalhama@gmail.com',
    license='BSD 2',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
        'Topic :: Text Processing',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        "Operating System :: OS Independent"
    ],
    project_urls={
        'Bug Reports': 'https://github.com/BramVanroy/spacy_conll/issues',
        'Source': 'https://github.com/BramVanroy/spacy_conll',
    },
    python_requires='>=3.6',
    entry_points={
        'console_scripts': ['main_parse=spacy_conll.__main__:main']
    }
)
