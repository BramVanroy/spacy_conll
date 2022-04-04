from pathlib import Path
from setuptools import find_packages, setup

from spacy_conll import __version__

extras = {
    "pd": ["pandas"],
    "parsers": ["spacy-udpipe>=1.0.0", "spacy-stanza>=1.0.0"]
}
extras["all"] = extras["pd"] + extras["parsers"]
extras["dev"] = extras["all"] + ["pytest", "flake8", "isort", "black", "pygments"]

setup(
    name="spacy_conll",
    version=__version__,
    description="A custom pipeline component for spaCy that can convert any parsed Doc"
                " and its sentences into CoNLL-U format. Also provides a command line entry point.",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    keywords="nlp spacy spacy-extension conll conllu tagging parsing stanza spacy_stanza udpipe spacy_udpipe",
    packages=find_packages(include=["spacy_conll", "spacy_conll.*"]),
    url="https://github.com/BramVanroy/spacy_conll",
    author="Bram Vanroy",
    author_email="bramvanroy@hotmail.com",
    license="BSD 2",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Topic :: Text Processing",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent"
    ],
    project_urls={
        "Bug Reports": "https://github.com/BramVanroy/spacy_conll/issues",
        "Source": "https://github.com/BramVanroy/spacy_conll",
    },
    python_requires=">=3.6",
    install_requires=[
        "spacy>=3.0.1",
        "dataclasses;python_version<'3.7'"
    ],
    extras_require=extras,
    entry_points={
        "console_scripts": ["parse-as-conll=spacy_conll.cli.parse:main"],
        "spacy_factories": ["conll_formatter = spacy_conll.formatter:create_conll_formatter",
                            "disable_sbd = spacy_conll.utils:create_spacy_disable_sentence_segmentation"]
    }
)
