import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(__file__))

from mangum import Mangum
from app import app

# Create the Lambda handler
handler = Mangum(app)
