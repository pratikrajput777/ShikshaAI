# The User model has been consolidated into the 'users' app.
# This file is intentionally left blank to avoid model clashes.
from django.contrib.auth import get_user_model
User = get_user_model()


