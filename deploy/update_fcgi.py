#!/usr/bin/python
"""
Script used to update application code for flup.

It is not enough to touch the configuration .fcgi file. This script moves it to [random_string].fcgi and updates .htaccess accordingly.
It must be run from the directory where .fcgi file and .htaccess are.
"""

import random
import re
import shutil

# read current htaccess data
f = open('.htaccess','r')
htaccess = f.read()
f.close()
# fetch current fcgi name
p = re.compile('/([^/ ]*).fcgi')
s = p.search(htaccess)
name = s.group(1)
# build new random name
refstr='abcdefghijklmnopqrstuvwxyz'
new_name = ''.join([random.choice(refstr) for i in xrange(5)])
# update htaccess
p = re.compile(name)
htaccess = p.sub(new_name, htaccess)
f.close()
f = open('.htaccess','w')
f.write(htaccess)
f.close()
# replace fcgi file
shutil.move("./%s.fcgi" % name,"./%s.fcgi" % new_name)

