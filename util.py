import os

def makeconf():
    'create an empty conf file'

    conf_file = 'conf.py'

    if os.path.exists(conf_file):
        print 'conf.py already exists'
        raise SystemExit

    contents = '''\
# Change configuration settings here.
# See defaults.py for the default settings

from defaults import *


'''

    f = open(conf_file, 'w')
    f.write(contents)
    f.close()

    print 'conf.py created'
    print 'please check configuration.'


from collections import defaultdict

class defaultNonedict(defaultdict):
    def __missing__(self, key):
        return None
