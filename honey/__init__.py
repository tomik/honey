from core import app
import views

import sys
print filter(lambda p: not "python" in p, sys.path)
