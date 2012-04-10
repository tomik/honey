#!/usr/bin/python2.6

import os
os.environ["PATH"] = "/bin"

activate_this = '/home/tomik/public/www/senseicrowd/env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

from flup.server.fcgi import WSGIServer
from honey import app

# handle scriptname.fcgi suffix
class ScriptNameStripper(object):
    def __init__(self, app):
        self.app = app
        self.pat = r"/[a-z]*.fcgi"
    def __call__(self, environ, start_response):
        import re
        environ['SCRIPT_NAME'] = re.sub(self.pat, "", environ.get("SCRIPT_NAME", ""))
        return self.app(environ, start_response)

# and on the production environment activate this middleware, make sure
# to not do that during development with the integrated server.
app.wsgi_app = ScriptNameStripper(app.wsgi_app)

if __name__ == '__main__':
    WSGIServer(app).run()
