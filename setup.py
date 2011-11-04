from setuptools import setup, find_packages
#from distutils.core import setup



data_files = [
    ('/usr/share/applications', ['docktask.desktop']),
    ('/usr/share/pixmaps', ['docktask/docktask.png']),
    ]

setup(name='docktask',
      version='0.0.0',
      author='LI Daobing',
      author_email='lidaobing@gmail.com',
      url='http://github.com/lidaobing/docktask',
      data_files = data_files,
      scripts = ['scripts/docktask'],
      packages = ['docktask'],
      package_data={'': ['*.png']},
      include_package_data = True,
      )
