# ToriScan
Live version is available at: https://t.me/ToriScan_bot

ToriScan is the bot that helps you stay updated with new listings on Tori.fi. Get instant (almost) notifications on Telegram whenever new items matching your search criteria are posted.

Please note: That's a pet non-profit project. ToriScan and/or it's developer is not affiliated with tori.fi or Schibsted Media Group in any way.

# How to launch
1. Install the dependencies:
(you need to have Python installed)
``` pip install --upgrade -r requirements.txt ```
2. Obtain the token for your own bot:
You can do it using https://t.me/BotFather. It will guide you throught the process.
3. Put your token to bot.py:
[Here](https://github.com/arealibusadrealiora/tori-scan-bot/blob/main/bot.py#L22) you should set up the token you've obtained in the previous step ("token" variable). You have a couple of options on how to do it:
    - Set it as a environment variable. (Default option. For Windows, you can look for instructions [here](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-powershell-1.0/ff730964(v=technet.10)?redirectedfrom=MSDN), for Linux use echo ``` "TOKEN=your_token" > .env ```);
    - Put it as a token.txt in the same folder with the bot.py;
    - Hard-code it (``` token = your_token ```).
4. Launch:
``` python bot.py ``` 

Alternatively, if you're familiar with Docker, you can simply use the Dockerfile from this repo.
