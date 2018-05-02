from setuptools import setup, find_packages

# setup_path = pathlib.Path(os.path.dirname(os.path.relpath(__file__)))
# with open(setup_path.joinpath('README.md').as_posix(), encoding='utf-8', mode='r') as f:
#     long_description = f.read()

setup(name='lib-cli',
      version='0.0.1',
      packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
      install_requires=[
          'Click==6.7',
          'colorama==0.3.9',
          'redis==2.10.6',
          'pymongo==3.6.1',
          'neo4j-driver==1.5.0'
      ],
      python_requires='>=3.5',
      entry_points={
          'console_scripts': [
              'lib-redis=library_cli.redis.redis_lib:cli',
              'lib-mongo=library_cli.mongo.mongo_lib:cli',
              'lib-neo=library_cli.neo4j.neo4j_lib:cli'
          ]
      },
      include_package_data=True)
