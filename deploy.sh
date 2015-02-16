#!/bin/bash

sudo rm -rf $INDUS_HOME/lib/net
sudo cp -r net $INDUS_HOME/lib
sudo chown -R root:indus $INDUS_HOME/lib/net
sudo chmod -R 770 $INDUS_HOME/lib/net

#0
