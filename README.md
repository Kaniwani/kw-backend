![](https://travis-ci.org/tadgh/KW.svg)


# KW
KaniWani

Getting started:
Since we're using Django, a fair bit of setup is required to get a development environment up and running. Here are all the tools you need. 

1. Python 3. [You can get it from activestate](http://www.activestate.com/activepython/downloads)
2. If you want to use the distributed messaging queue for tasks, [install RabbitMQ Server](http://www.rabbitmq.com/download.html). This is only necessary if you want to use the periodic features(for example having the SRS run every 15 minutes).
3. Install Pycharm(really, it makes everything much easier)
4. Clone the repository wherever you like.
5. Move the **secrets.py** file into the same directory as the **settings.py** file. 
6. Fire up pycharm and open the parent KW directory. 
7. After a bit, there should be a prompt to install a list of requirements, hit yes and let the installation go. It'll give you a popup when it is done.
8. Delete the db.sqlite3 file 
9. hit Ctrl + alt + r . This will open up a manage.py command window. 
10. execute the command **syncdb**
11. It will prompt you to create a superuser, do so. 
12. Ctrl + alt + r again. 
13. This time execute **migrate**. The database is now built, but not yet populated. 
14. Ctrl + alt + r again. 
15. Exeute the command **shell**. This brings you to application shell.
16. Execute this:

```python
from kw_webapp.db_repopulator import repopulate
repopulate()
```
Chances are your system will spit a bunch of errors at you. Ignore them and wait. Eventually they will stop. 

17. In the settings.py file, chances are you will fine `DEBUG = False`, change this to `DEBUG = True`
18. Ctrl + alt + r one last time. Type in the command **runserver**

If all went well, it will start a server at 127.0.0.1:8000
