# injects.py
Simple script to auto post injects to discord and scoring engine

![Example](https://raw.githubusercontent.com/DSU-DefSec/injects.py/master/example.png)

## Configs:
#### injects.json:
```json
{
  "injects": [
    {
      "name": "Name of inject",
      "desc": "Description of inject",
      "post": "hh:mm",
      "due": "16:00",
      "priority": "medium"
    }
  ]
}
```

`priority` from `critical, high, medium, low, info` changes color of embed

#### config.json:

```json
{
  "discord": "https://discordapp.com/api/webhooks/##################/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "discord_content": "Whatever you want in the discord message content (not the embed)",
  "close_enough": 2,
  "comp_date": "2021-02-12",
  "comp_tz": "US/Central"
}
```

`close_enough` is max seconds before the post time that it can post it. (Ignored by all and specific)
`comp_tz` timezone name the competition will be in


## Usage:
#### Standalone:
Will wait until the right time then post injects  
Updates `state.json` as it goes. Will start back up in the same spot if restarted
```
$ python3 injects.py
```

#### Single run:
Will post any injects that should be posted after the last posted `state.json` and before the current time then exit  
Could crontab this if you dont want the script always running
```
$ python3 injects.py <literally anything but a number and all>
$ python3 injects.py tacocat
```

#### Specific inject:
Will post specific inject and exit ignoring `state.json`
```
$ python3 injects.py <inject number>
$ python3 injects.py 3
```

#### All injects:
Will post all injects ignoring `state.json` (requires confirmation)
```
$ python3 injects.py all
```