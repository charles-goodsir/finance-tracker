import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(__file__))

# Set environment variable to indicate we're in Lambda
os.environ["AWS_LAMBDA_FUNCTION_NAME"] = "FinanceTrackerFunction"

from mangum import Mangum
from app import app

# Create the Lambda handler
handler = Mangum(app)
