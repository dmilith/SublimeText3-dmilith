import os
import sys
import json

json.dump(dict(os.environ), sys.stdout, indent=4)