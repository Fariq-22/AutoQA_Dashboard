from dotenv import load_dotenv
import os
load_dotenv() 


MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_NAME = os.getenv("MONGODB_NAME")

SECRET_KEY = os.getenv("SECRET_KEY")