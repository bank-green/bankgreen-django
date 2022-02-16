# Bank Green Django App

This is a [python django](https://www.djangoproject.com/) application for cataloging and creating environmental ratings of worldwide banks.

Data is harvested from a variety of "data sources." Datasources are then associated with "brands." One brand may be comprised of zero, one, or many data sources.

# Installation and Development

You will need to install "[pip](https://pip.pypa.io/en/stable/installation/)" (the python package management system) and "[pipenv](https://pypi.org/project/pipenv/)" (a python virtualen environment manager) to your system.

## Installing Packages

`pipenv install`

## Activating the virtual environment

`pipenv shell`

## Installing packages

`pipenv install [PACKAGENAME]`

## Deactivating the virtual environment

`deactivate`

# Usage

## Run the administrator panel

```
python manage.py runserver
```

## Refreshing Data

### Refresh datasources from API

```
# python manage.py refresh_datasources [DATASOURCE_NAME]
# i.e.
python manage.py refresh_datasources banktrack
# or
python manage.py refresh_datasources all
```

### Refresh datasources from local

```
# python manage.py refresh_datasources [DATASOURCE_NAME] --local [DATASOURCE_NAME]
# i.e.
python manage.py refresh_datasources banktrack --local banktrack
```
