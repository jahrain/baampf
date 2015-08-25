from distutils.core import setup

setup(name='baampf',
      version='0.1',
      description='Bulk apply artwork to MP3 files',
      author='Jahrain',
      url='https://github.com/jahrain/baamf',
      install_requires=['PyID3','PIL'],
      dependency_links=['git+https://github.com/myers/pyid3.git'],
      scripts=['baampf.py'])
