from datetime import datetime, timedelta
from .models import *


def check_expired_data():
    try:
        result = News.objects.filter(
            posting_date__lte=datetime.now() - timedelta(days=30)
        ).delete()
    except Exception as e:
        print("ERROR=", e)

    print("Deleted:", result)
