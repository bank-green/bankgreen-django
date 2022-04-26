import json
from datetime import datetime, timezone

from django.db import models

import requests

from datasource.models.datasource import Datasource, classproperty


class Usnic(Datasource):
    """ """

    @classproperty
    def tag_prepend_str(cls):
        return cls.__name__.lower() + "_"
