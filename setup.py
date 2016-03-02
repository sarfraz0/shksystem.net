from setuptools import setup

setup(name='shksystem.net',
      version='0.1.9.15',
      author='Sarfraz Kapasi',
      author_email='sarfraz@variablentreprise.com',
      license='GPL-3',
      packages=[
                 'net'
               , 'net.shksystem'
               , 'net.shksystem.common'
               , 'net.shksystem.db'
               , 'net.shksystem.web'
               , 'net.shksystem.web.users'
               ],
      install_requires=[ 'tornado'
                       , 'sqlalchemy'
                       , 'psycopg2cffi'
                       , 'passlib'
                       , 'futures'
                       ],
      include_package_data = True,
      zip_safe =False)

