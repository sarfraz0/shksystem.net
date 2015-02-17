#!/usr/bin/env python

### Author : Sarfraz Kapasi
### Date   : 09.02.2015

import os
import csv
from sqlalchemy      import create_engine
from sqlalchemy.orm  import sessionmaker
from liv_deploy      import Base
from liv_deploy      import Component, Computer, Rule

# ../conf/liv_deploy.db
sqlite_fic = os.path.join(os.path.abspath('../conf'), 'liv_deploy.db')
engine     = create_engine('sqlite:///' + sqlite_fic.replace('\\', '\\\\'))
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
s       = Session()

## Lecture csv
compo_fic = os.path.join(os.path.abspath('../conf'), 'components.csv')
compu_fic = os.path.join(os.path.abspath('../conf'), 'computers.csv')
rules_fic = os.path.join(os.path.abspath('../conf'), 'rules.csv')

## Ajout des composants
i = 1
with open(compo_fic, 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        s.add(Component(i, row[0], row[1]))
        i += 1
    s.flush()

## Ajout des serveurs
with open(compu_fic, 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        s.add(Computer(row[0], row[1], row[2], row[3]))
    s.flush()

## Ajout des regles
with open(rules_fic, 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        s.add(Rule(row[0], row[1], row[2], row[3], row[4], int(row[5])))
    s.flush()

s.commit()
#0
