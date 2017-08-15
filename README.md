![Build Status](https://travis-ci.org/Kaniwani/KW-Backend.svg)
[![Deployment status from DeployBot](https://kaniwani.deploybot.com/badge/66802254069768/57929.svg)](http://deploybot.com)

# KW
KaniWani

### Getting started:
#### Backend (docker)
Docker enables you to setup a development environment automatically. Docker can be [downloaded from here](https://docs.docker.com/engine/installation/#desktop)

Execute the following commands:
```sh
# Clone the repository
git clone https://github.com/Kaniwani/kw-backend.git && cd kw-backend
# Start the redis server, django server and run migrations
docker-compose up --build
```

A webserver should be running on http://localhost:8000

##### Populate the database
Open an interactive python shell with the following command:
```sh
docker-compose run --rm web python3 manage.py shell
```

Run the following python code inside the shell:
```python
from kw_webapp.tasks import repopulate
repopulate()
```

#### Backend (manual)
Since we're using Django, a fair bit of setup is required to get a development environment up and running. Here are all the tools you need.

1. Python 3. [You can get it from activestate](http://www.activestate.com/activepython/downloads)
2. If you want to use the distributed messaging queue for tasks, [Install a redis server](http://redis.io/) This is only necessary if you want to use the periodic features(for example having the SRS run every 15 minutes).
3. Install Pycharm (or use whatever editor you like).
4. Clone the repository wherever you like.
5. Move the **secrets.py** file into the same directory as the **settings.py** file.
6. Fire up pycharm and open the parent KW directory.
7. After a bit, there should be a prompt to install a list of requirements, hit yes and let the installation go. It'll give you a popup when it is done.
7b. If this doesn't happen, and you know your way around the terminal, try *pip install -r requirements.txt*
8. Delete the db.sqlite3 file
9. hit Ctrl + alt + r . This will open up a manage.py command window.
10. execute the command **makemigrations**
11. It may prompt you to create a superuser, do so.
12. Ctrl + alt + r again.
13. This time execute **migrate**. The database is now built, but not yet populated.
14. Ctrl + alt + r again.
15. Exeute the command **shell**. This brings you to application shell.
16. Execute this:

```python
from kw_webapp.tasks import repopulate
repopulate()
```
Chances are your system will spit a bunch of errors at you. Ignore them and wait. Eventually they will stop.

17. Ctrl + alt + r one last time. Type in the command **runserver --noreload**

If all went well, it will start a server at 127.0.0.1:8000

#### Frontend
Here are all the tools you'll need.

1. Node.js [Get it here] (https://nodejs.org).
2. NPM (installed with Node, huzzah) (does this step even count?).
3. Open a terminal, navigate to the frontend folder, and run `npm install`.
4. Make some tea while you wait.
5. When dependencies are installed, run `gulp` to see styleguide & watch changes.

This will start a server at localhost:3000 & open your browser to the styleguide.

However, *to compile & copy assets to be accessed within the webapp* ensure you run `gulp --prod`

More detailed information in `/_front-end/README.MD`
