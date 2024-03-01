deploy:
    ssh bankgreen "\
    cd /home/django/bankgreen-django; \
    source venv/bin/activate && \
    git pull && \
    pip install -r requirements.txt && \
    python manage.py migrate && \
    sudo systemctl restart gunicorn && \
    sudo systemctl status gunicorn \
    "
    