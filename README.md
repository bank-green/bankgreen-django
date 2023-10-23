# Bank Green Django App

This is a [python django](https://www.djangoproject.com/) application for cataloging and creating environmental ratings of worldwide banks.

Data is harvested from a variety of "data sources." Datasources are then associated with "brands." One brand may be comprised of zero, one, or many data sources.

# Installation and Development

This project uses python 3.10. You will need to install "[pip](https://pip.pypa.io/en/stable/installation/)" (the python package management system) and "[virtualenv](https://virtualenv.pypa.io/en/latest/installation.html)" (a python virtual environment manager) to your system. You can install virtualenv like: `sudo -H pip3 install virtualenv`


## Creating a virtual environment \<venv\>

`virtualenv <venv>`

## Activating the virtual environment

`source <venv>/bin/activate`

## Installing packages

`pip install -r requirements.txt`

## Deactivating the virtual environment

`deactivate`

## Environment variables
There's an .env file in the same path as settings.py where all environment variables are and should be placed. You should *call* them in settings.py and then import them like settings.KEYWORD

`cp bankgreen/.env.template bankgreen/.env`

## Monitoring

Monitoring is done via [Django Prometheus](https://github.com/korfuri/django-prometheus). To set this up locally, do the following:

1. Download and install [Prometheus](https://prometheus.io/docs/introduction/first_steps/). Prometheus should be in a separate directory from the Bank Green Django application.
2. In `prometheus.yml`, replace the `scrape_configs` section with:
```
scrape_configs:
  - job_name: bank-green
    scrape_interval: 10s

    static_configs:
      - targets: ["localhost:8000"]
```
## Running Prometheus

In your Prometheus directory, run: `./prometheus --config.file=prometheus.yml`.

To query metrics graphs, go to localhost:9090.

## Database
To setup the database, you must run migrations, add sample data by installing the initial fixture and download a list of countries and regions:   
`python manage.py migrate`   
`python manage.py loaddata fixtures/initial/initial.json`   
`python manage.py cities_light`   

Then create a superuser:   
`python manage.py createsuperuser`

## Django commands

```
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
python manage.py refresh_datasources banktrack --local all
python manage.py cities_light # refresh country/region database
python manage.py runserver
```

## Nginx and Gunicorn userful commands

```
sudo systemctl stop/start/restart nginx
sudo nginx -t
sudo tail -F /var/log/nginx/error.log

sudo systemctl status gunicorn.socket
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
sudo journalctl -u gunicorn.socket
```
## Formatting

To automagically format your code, run `black .` from the root of the repo.

## Refreshing Data

### Updating initial fixture
This assumes that only the data wanted for the initial fixture is in the current database. To update the initial fixture, run `python3 manage.py dumpdata --indent 4 > fixtures/initial/initial.json`. Remove internal django model entries from initial.json added to the database by running `python fixtures/initial/remove_django_internals.py` script. Specifically, this means any entries for the 'django_content_type' table, which has a UNIQUE constraint on it's fields, but more generally, refers to any internal Django tables not explicitly defined in the various models.   

### Updating cities_light fixtures
```
django dumpdata cities_light.Subregion --indent 4 > fixtures/citieslight/subregion.json
```

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

### Suggest Associations between brands and datasources
_This is currently only implemented for USNIC datasources. Running may take between 1 and 10 minutes_
```
django manage.py suggest_associations
```

## Rate limit in Nginx
Rate limit for endpoint **/graphql** is 10 request/sec for every IP.
To disable it do: `sudo nano etc/nginx/sites-available/bankgreen` and comment out or delete this part:
```
location /graphql {
        limit_req zone=ddos_limit;
        limit_req_status 429;
        include proxy_params;
        proxy_pass http://unix:/home/django/gunicorn.sock;
    }
```
`limit_req_zone $binary_remote_addr zone=ddos_limit:10m rate=10r/s;` This is the part where **ddos_limit** is defined.

Then restart Nginx and Gunicorn:
`sudo systemctl restart nginx && sudo systemctl restart gunicorn`
