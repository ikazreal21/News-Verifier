from datetime import datetime, timedelta
from .models import *

def check_expired_data():
    News.objects.filter(posting_date__lte=datetime.now()-timedelta(minute=1)).delete()
    print("deleted")