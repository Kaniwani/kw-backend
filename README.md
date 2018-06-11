![Build Status](https://travis-ci.org/Kaniwani/KW-Backend.svg)
[![Deployment status from DeployBot](https://kaniwani.deploybot.com/badge/66802254069768/57929.svg)](http://deploybot.com)

# KW
KaniWani

### Getting started:
#### Backend
Since we're using Django, a fair bit of setup is required to get a development environment up and running. Here are all the tools you need.

1. Python 3. [You can get it from activestate](http://www.activestate.com/activepython/downloads)
2. If you want to use the distributed messaging queue for tasks, [Install a redis server](http://redis.io/) This is only necessary if you want to use the periodic features(for example having the SRS run every 15 minutes).
3. Install Pycharm (or use whatever editor you like).
4. Clone the repository wherever you like.
5. Open the `settings.py` file and set the default databases in `DATABASES`. For example, if you want a local SQLite DB, set `default` to the following:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3'
    }
}
```
The default configuration uses PostgreSQL locally.

6. Fire up Pycharm and open the parent KW directory.
7. After a bit, there should be a prompt to install a list of requirements, hit yes and let the installation go. It'll give you a popup when it is done.
7b. If this doesn't happen, and you know your way around the terminal, try `pip install -r requirements.txt`
8. Delete the db.sqlite3 file if it exists.
9. Hit Ctrl + Alt + R . This will open up a manage.py command window. If not using Pycharm, navigate to the root directory of the project in a terminal.
10. Execute the command `makemigrations`. If not using Pycharm, run `python manage.py makemigrations` in your open terminal.
11. It may prompt you to create a superuser, do so.
12. Ctrl + Alt + R again.
13. This time execute `migrate`. If not using Pycharm, run `python manage.py migrate` in your open terminal. The database is now built, but not yet populated.
14. Ctrl + Alt + R again.
15. Execute the command `shell`. If not using Pycharm, run `python manage.py shell` in your open terminal. This brings you to application shell.
16. Execute this:

```python
from kw_webapp.utils import repopulate
repopulate()
```
The app will now build the local database based off of WK's. Chances are your system will spit a bunch of errors at you. Ignore them and wait. Eventually they will stop.

17. (subject to change!) Now you need to import supplemental data that isn't synced from WK. Execute the following in the `shell`:
```python
from kw_webapp.utils import one_time_import_jisho_new_format
one_time_import_jisho_new_format("wk_vocab_import.json")
```
The app will now import a bunch of additional data from the local `wk_vocab_import.json` file. This will take quite some time, so sit tight.

18. Ctrl + Alt + R one last time. Type in the command `runserver --noreload` (`python manage.py runserver --noreload` if using a terminal).

If all went well, it will start a server at 127.0.0.1:8000

