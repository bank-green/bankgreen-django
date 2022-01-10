import json
import requests
from datetime import datetime, timezone

from django.db import models


from datasource.models.datasource import Datasource


class Custombank(Datasource):
    """
    Custombank is custom entered data that always wins during merges.
    """

    comment = models.TextField()
