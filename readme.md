# aschedule

[![build status][2]][1] [![coverage][3]][1] [![codacy][5]][4] [![mitlicence][7]][6]

Python asyncio Job Scheduling.

aschedule (async schedule) allows you to schedule python co-routines periodically or
at a specific time.

### Install
```bash
pip install aschedule==0.0.2.dev0
```

### Quick Start

###### Print most cpu consumption percentage every second
```python
import asyncio, psutil
import aschedule

async def print_cpu():
    # send an email to the users
    print('report', round(loop.time()), ':', psutil.cpu_percent())

schedule = aschedule.every(print_cpu, seconds=1)
loop = asyncio.get_event_loop()
loop.run_until_complete(schedule.future)
```

###### Send a message to developer's telegram account about website's analytics

```python
BOT_TOKEN, CHAT_ID = '123456789:ABC_DEFGHJsfafs-fasdfs32sdfs7sEW', 124254321
import aiohttp, json
import aschedule

URL = 'https://api.telegram.org/bot{}/sendmessage'.format(BOT_TOKEN)
number_of_requests = 0

async def send_stats():
    payload = {
        'chat_id': CHAT_ID,
        'text': str(number_of_requests),
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(URL, params=payload) as response:
            print(await response.text())  # log the reponse

async def handle(request):
    global number_of_requests
    number_of_requests += 1
    text = "Hello, " + request.match_info.get('name', "Anonymous")
    return aiohttp.web.Response(body=text.encode('utf-8'))

app = aiohttp.web.Application()
app.router.add_route('GET', '/{name}', handle)

aschedule.every(send_stats, seconds=30)  # send stats to the developer every 30 seconds

aiohttp.web.run_app(app)
```

###### Send an email to the users everyday

```python
import asyncio
import aschedule

async def send_email_to_users():
    # send an email to the users
    pass

schedule = aschedule.every(send_email_to_users, days=1)
asyncio.get_event_loop().run_until_complete(schedule.future)
```

### Testing

```bash
nosetests --with-coverage --cover-package=aschedule --cover-min-percentage=90 --cover-config-file=.coveragerc --processes=50 --process-timeout=600 --cover-inclusive
```

[1]: https://gitlab.com/eightnoteight/aschedule/builds
[2]: https://gitlab.com/eightnoteight/aschedule/badges/master/build.svg
[3]: https://gitlab.com/eightnoteight/aschedule/badges/master/coverage.svg
[4]: https://www.codacy.com/app/eightnoteight/aschedule
[5]: https://api.codacy.com/project/badge/Grade/d505fa35e59a4c52937302fc63190487
[6]: https://gitlab.com/eightnoteight/aschedule/blob/master/license
[7]: https://img.shields.io/badge/license-MIT-blue.svg
