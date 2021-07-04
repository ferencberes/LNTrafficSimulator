from setuptools import find_packages, setup

install_requires = [
    "pandas",
    "numpy",
    "networkx",
    "matplotlib",
    "seaborn",
    "tqdm",
]

#setup_requires = ['pytest-runner']

#tests_require = [
#    'pytest',
#    'pytest-cov',
#    'codecov'
#]

keywords = [
    "bitcoin",
    "lightning-network",
    "simulator",
    "simulation",
    "research",
    "cryptoeconomics"
]

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='lnsimulator',
      version='0.1.0',
      description="Traffic Simulator for Bitcoin's Lightning Network ",
      url='https://github.com/ferencberes/LNTrafficSimulator',
      author='Ferenc Beres',
      author_email='fberes@info.ilab.sztaki.hu',
      packages = find_packages(),
      install_requires=install_requires,
      #setup_requires = setup_requires,
      #tests_require = tests_require,
      keywords = keywords,
      long_description=long_description,
      long_description_content_type='text/markdown',
)
