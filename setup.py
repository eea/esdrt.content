import os

from setuptools import find_packages
from setuptools import setup

version = "1.74.5"

setup(
    name="esdrt.content",
    version=version,
    description="Content-types for ESD Review Tool",
    long_description=open("README.txt").read()
    + "\n"
    + open(os.path.join("docs", "HISTORY.txt")).read(),
    # Get more strings from
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="",
    author="Mikel Larreategi",
    author_email="mlarreategi@codesyntax.com",
    url="https://github.com/eea/esdrt.content/",
    license="GPL",
    packages=find_packages(exclude=["ez_setup"]),
    namespace_packages=["esdrt"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "setuptools",
        "five.grok",
        "plone.app.dexterity [grok, relations]",
        "plone.namedfile [blobs]",
        "collective.z3cform.datagridfield",
        "plone.api",
        "Products.ATVocabularyManager",
        "plone.app.versioningbehavior",
        "plone.app.workflowmanager",
        "cs.htmlmailer",
        "collective.deletepermission",
        "tablib",
        "python-docx == 0.8.5",
        "zc.dict",
        "collective.monkeypatcher",
        "python-ldap",
        "Products.LDAPUserFolder",
        "openpyxl",
    ],
    entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
)
