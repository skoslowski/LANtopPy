LANtopPy
========

This python package provides a client API and CLI to control/manage *Theben* digital time switches with a yearly program *TR 64x top2* and a *EM LAN top2* module ([Theben product page][0]).

It allows to do almost all the stuff you can do with the *LAN_Modul* client software provided by *Theben*.
You can get general device info (time, ...) as well as get/set channel states, statistics and configs.
However, you can not read or write the schedules yet.

For development and tests a *TR 644 top2 RC* was used.
It should also work with other models and also the extension module *EM 4 top2*.

Also included are two tools that periodically fetch events from a Google Calendar and schedule certain channels to be activated during each event.
The (older) version is a script designed to be called via cron job. Its output is a crontab containing commands for the next week.
The newer version is a daemon with an internal scheduler. Extensive logging and support for PushBullet error notification included.

Legacy Python is not supported. Tested with Python 3.4.

[0]: http://www.theben.de/en/Products/TIME/Digital-time-switches/DIN-rail/Yearly-program/Yearly-program "Theben product page"
