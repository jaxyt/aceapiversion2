nohup gunicorn --bind 127.0.0.1:8000 aceapiversion2.wsgi:application --reload --access-logfile errlogs.log --workers=2 > my.log 2>&1 &
echo $! > save_pid.txt
