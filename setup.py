from setuptools import setup

setup(name='variablentreprise.com',
      version='0.1.8.4',
      author='Sarfraz Kapasi',
      author_email='sarfraz@variablentreprise.com',
      license='GPL-3',
      packages=[
                 'net'
               , 'net.shksystem'
               , 'net.shksystem.common'
               , 'net.shksystem.db'
               , 'net.shksystem.business'
               , 'net.shksystem.web'
               , 'net.shksystem.web.budget'
               , 'net.shksystem.web.budget.frt'
               ],
      install_requires=[ 'tornado'
                       , 'feedparser'
                       , 'transmissionrpc'
                       , 'requests'
                       , 'keyring'
                       , 'passlib'
                       , 'flask-login'
                       , 'flask-migrate'
                       , 'flask-wtf'
                       , 'celery'
                       , 'futures'
                       ],
      install_requires=[ 'tornado', 'keyring', 'passlib' ],
      include_package_data = True,
      zip_sae =False)
