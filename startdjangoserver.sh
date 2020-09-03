<<<<<<< HEAD
nohup gunicorn --bind 127.0.0.1:8000 aceapiversion2.wsgi:application --reload --workers=3 --access-logfile errlogs.log > my.log 2>&1 &
=======
nohup gunicorn --bind 127.0.0.1:8000 aceapiversion2.wsgi:application --reload --access-logfile errlogs.log --workers=2 > my.log 2>&1 &
>>>>>>> a41f63fc2dfe171f210a3e59bf26842553644bf0
echo $! > save_pid.txt
