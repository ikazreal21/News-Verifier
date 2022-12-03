from datetime import datetime, timedelta
from .models import *

def check_expired_data():
    News.objects.filter(posting_date__lte=datetime.now()-timedelta(days=7)).delete()