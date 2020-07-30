<<<<<<< HEAD
nohup gunicorn --bind 127.0.0.1:8000 aceapiversion2.wsgi:application --reload --access-logfile errlogs.log > my.log 2>&1 &
=======
nohup gunicorn --bind 127.0.0.1:8000 aceapiversion2.wsgi:application --reload --access-logfile errlogs.log --workers=3 > my.log 2>&1 &
>>>>>>> 60f5269a611a08e0241cf5c512833ef00c08b8b0
echo $! > save_pid.txt
