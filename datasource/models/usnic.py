import json
from datetime import datetime, timezone

from django.db import models

import requests

from datasource.models.datasource import Datasource


class Usnic(Datasource):
    """ """
