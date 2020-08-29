from distutils.core import setup

setup(name='lnsimulator',
      version='0.1',
      description="Traffic Simulator for Bitcoin's Lightning Network ",
      url='https://github.com/ferencberes/LNTrafficSimulator',
      author='Ferenc Beres',
      author_email='fberes@info.ilab.sztaki.hu',
      packages=['lnsimulator','lnsimulator.simulator'],
      install_requires=[
          "pandas",
          "numpy",
          "networkx",
          "matplotlib",
          "seaborn",
          "tqdm",
      ],
zip_safe=False)
