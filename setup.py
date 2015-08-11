from setuptools import setup

setup(name='shksystem.net',
      version='0.1.8.0',
      author='Sarfraz Kapasi',
      author_email='sarfraz@variablentreprise.com',
      license='GPL-3',
      packages=[ 'net'
               , 'net.shksystem'
               , 'net.shksystem.common'
               , 'net.shksystem.web'
               , 'net.shksystem.web.feed'
               , 'net.shksystem.web.blog'
               , 'net.shksystem.business'],
      include_package_data = True,
      zip_safe=False)
