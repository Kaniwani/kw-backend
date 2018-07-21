![Build Status](https://travis-ci.org/Kaniwani/KW-Backend.svg)
[![Deployment status from DeployBot](https://kaniwani.deploybot.com/badge/66802254069768/57929.svg)](http://deploybot.com)

# KW
KaniWani

## Getting started:

Getting the KaniWani backend up and running is pretty simple, but first you'll need to make sure you have [Docker]() and [`docker-compose`]() installed. Once you've installed Docker and `docker-compose` you should be ready to get started :tada:

To start the KaniWani backend just run:

```
> docker-compose up --detach # :rocket:
```

You should now be able to view the KaniWani API docs by browsing to `http://127.0.0.1:8000/docs/`! 

### First run

The first time you run `docker-compose` will take a while to download the service containers (Postgres, Adminer, and Redis) and build our Dockerfile. Subsequent runs should be really quick though. Now that your containers are running lets take a look at them. Run the following to see the stack: 

```
> docker ps
CONTAINER ID        IMAGE                   COMMAND                  CREATED             STATUS              PORTS                              NAMES
aea125aba4dd        kw-backend_kw-backend   "python3 manage.py r…"   9 minutes ago       Up 8 minutes        0.0.0.0:8000->8000/tcp             kw-backend_kw-backend_1
ea330cf79337        adminer                 "entrypoint.sh docke…"   9 minutes ago       Up 8 minutes        8080/tcp, 0.0.0.0:8080->8001/tcp   kw-backend_adminer_1
f786ac7434a3        redis:4.0               "docker-entrypoint.s…"   9 minutes ago       Up 8 minutes        0.0.0.0:6379->6379/tcp             kw-backend_redis_1
049a3da0810e        postgres:9.6            "docker-entrypoint.s…"   10 hours ago        Up 8 minutes        5432/tcp                           kw-backend_db_1
```

To conner to a container run `docker exec -it <container instance name> bash`. Let's connect to the KW backend container!

```
> docker exec -it kw-backend_kw-backend_1 bash
# <- This is the container terminal! 
```

Since this is the first run we will need to apply our migrations and populate the database with our vocab. Django gives us to tools to do this. To open the Django management shell and import our data run:

```
# ./manage.py migrate
# ./manage.py shell
>>> from kw_webapp.utils import repopulate
>>> repopulate()
# A lot of stuff is going to happen here and you may see some errors. Don't panic unless things explode :boom:
>>> from kw_webapp.utils import one_time_import_jisho_new_format
>>> one_time_import_jisho_new_format("wk_vocab_import.json")
# A lot more things flying by on the terminal. This shouldn't take long but you might as well stretch!
```

Sweeeeet! Now you have some data. To check it you can open [Adminer]() at https://localhost:8001. Adminer is a simple SQL UI. To login select Postgres as the DB type, `kanawani` as the database, username as the username, and password as the password. This is great for development, but obviously not to be used in prod. Have fun ;) 
