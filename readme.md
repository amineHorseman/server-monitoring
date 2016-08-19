# Server Monitoring

This package provides a lightweight python package to check the status of your server and send you a mail if there's a problem. This package will:
- Monitor your services
- Restart a service if it's down, and send you a mail notification
- Check if the websites hosted in your server are reachable 
- Send you a daily mail if everything goes well

The current design aims to make it simple and light in order to avoid overwhelming your server.

## Dependencies

```
pip install --upgrade subprocess
pip install --upgrade sh
```

## How to use?

This package is composed of 2 scripts that can run both in the same machine, or in 2 different machines. 
- The service provider script  will continuously run in the server, listen to our requests, check the services, restart them if necessary, and send the list of hosted websites.
- The service client script will send requests to the monitoring script, check the availability of the hosted websites, and send us mail alerts. It's better to run it from a different machine (since we want also to be notified if our server is down). 

### 1. Server side

First edit the *hosted-websites.txt* file and add your websites (one per each line).

You may also modify some variables in the *server_monitoring.py* script:
```
# listening port
PORT = 11350
# list of the services to check
SERVICES_TO_MONITOR = ['apache2', 'cron', 'mysql', 'fail2ban']
# set a password to reject the other persons from checking your running services
AUTH_CODE = "password"   # it's not a perfect security, but it's better than nothing xD
```

Now, run the service provider in the background:
```
python service_provider/server_monitoring.py &
```

### 2. Client side

You need first to configure some variables in the *server_checker.py*:
```
# your mail address
DESTINATION_MAIL_ADDRESS = "admin@mail.com"
# the adress that will be displayed in your mailbox
MAIL_ADDRESS = "alerts@yourserver.com"
# the IP address of your server, the listening port and the AUTH_CODE
REMOTE_SERVER_IP = "127.0.0.1"
PORT = 11350
AUTH_CODE = "password"
```

Now, execute this script each time you want to check the status of your server (services states & websites):
```
python server_checker.py 
```

### 3. Configure cron jobs (optional, but recommended)

It's more interessting if we configure a recurrent cron job to execute our scripts automatically.

To do to this, open the crontab file first:
```
sudo crontab -e
```

The following line will add a cron job to start our service_provider (server side) when the system starts:
```
@reboot python ~/server_monitoring/service_client/service_provider/server_monitoring.py &
```

The following one, will add a cron job that will execute automatically the service_checker (client side) every X minutes. This way we will be notified as soon as possible if there's a problem.
```
*/10 * * * * python ~/server_monitoring/service_client/server_checker.py &
```
In this example I set X = 10 minutes. You can choose any value you want.

### Important notes: 
- Don't forget to specify the absolute path of your scripts. In this example, we assume our package is located in the home directory.
- The server_checker (client side) can be run locally in the server, but I think it's better to run it in another machine, since we want also to get notified if our server is down.
- If there's a problem, you'll be notified by mail. But it's possible that the mail will be classified as a SPAM. Make sure to add the server's MAIL_ADDRESS to your mailing contacts.
- If nothing's wrong, the script will send you a daily status mail. If you don't receive the daily mail, this means that your mailing service is probably down.
- Don't forget to add a empty line at the end of the crontab file, this will avoid you some useless troubleshooting LOL.

