![Build Status](https://travis-ci.org/Kaniwani/KW-Backend.svg)
[![Deployment status from DeployBot](https://kaniwani.deploybot.com/badge/66802254069768/57929.svg)](http://deploybot.com)

# KW
KaniWani

## Getting started:

Getting the KaniWani backend up and running is pretty simple, but first you'll need to make sure you have [Docker]() and [`docker-compose`]() installed. Once you've installed Docker and `docker-compose` you should be ready to get started :tada:

To start the KaniWani backend just run:

```
> docker-compose up --detach
```

You should now be able to view the KaniWani API docs by browsing to `http://127.0.0.1:8000/redoc/`! 

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

To connect to a container run `docker exec -it <container instance name> bash`. Let's connect to the KW backend container!

```
> docker exec -it kw-backend_kw-backend_1 bash
# <- This is the container terminal! 
```

Since this is the first run we will need to apply our migrations and populate the database with our vocab. Django gives us to tools to do this. To open the Django management shell and migrate the database run:

```
# ./manage.py migrate
```
To populate the database, you'll need to sync from Wanikani using a real API (v2) key. First, create an account:
1. This is easiest done via the UI
   * Head over to [the kw-frontend repository](https://github.com/Kaniwani/kw-frontend) for instructions on how to run a local instance
   * Register a new user via the "Register" tab on the welcome page of your local instance
1. If you're feeling adventurous, you can do this through the backend shell instead
    * Run the following in the backend container:
```
# ./manage.py shell
>>> from api.sync.SyncerFactory import Syncer
>>> from kw_webapp.models import Profile
>>> from django.contrib.auth.models import User
>>> my_user = User(username="my_username")
>>> my_user.set_password("securepassword123")
>>> my_user.save()
>>> my_profile = Profile(api_key_v2="YOUR_API_KEY_HERE", user=my_user)
>>> my_profile.save()
>>> syncer = Syncer.factory(my_profile)
>>> syncer.sync_top_level_vocabulary()
# A lot of stuff is going to happen here and you may see some errors. Don't panic unless things explode :boom:
```
   * After that's done, the db should be populated!

Finally, if you need the integrated jisho data for some reason, reach out to the maintainers and get a file named "wk_vocab_import.json". Put that file in the kw-backend root directory; then, back in your container shell, run:
```
# ./manage.py shell
>>> from kw_webapp.utils import one_time_import_jisho_new_format
>>> one_time_import_jisho_new_format("wk_vocab_import.json")
# A lot more things flying by on the terminal. This shouldn't take long but you might as well stretch!
```

Sweeeeet! Now you have some data. To check it you can open [Adminer](https://www.adminer.org/) at http://localhost:8001. Adminer is a simple SQL UI. To login select Postgres as the DB type, `kaniwani` as the database, `kaniwani` as the username, and `password` as the password (from `docker-compose.yml`). This is great for development, but obviously not to be used in prod. You can also connect to Redis at the default port (6379) and `redis-cli`.

Have fun ;) 
