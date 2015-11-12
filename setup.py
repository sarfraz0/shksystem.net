from setuptools import setup

setup(name='shksystem.net',
      version='0.1.8.4',
      author='Sarfraz Kapasi',
      author_email='sarfraz@variablentreprise.com',
      license='GPL-3',
      packages=[ 'net'
               , 'net.shksystem'
               , 'net.shksystem.common'
               , 'net.shksystem.web'
               , 'net.shksystem.web.feed'
               , 'net.shksystem.business'],
      install_requires=[ 'feedparser', 'transmissionrpc', 'requests', 'keyring', 'passlib', 'pandas', 'flask-login', 'flask-migrate', 'flask-httpauth', 'flask-wtf' ],
      include_package_data = True,
      zip_safe=False)
