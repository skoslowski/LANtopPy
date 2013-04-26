LANtopPy
========

This python package provides a client API and CLI to control/manage *Theben* digital time switches with a yearly program *TR 64x top2* and a *EM LAN top2* module ([Theben product page][0]).

It allows to do almost all the stuff you can do with the *LAN_Modul* client software provided by *Theben*. You can get general device info (time, ...) as well as get/set channel states, statistics and configs. However, you can not read or write the schedules yet.

For development and tests a *TR 644 top2 RC* was used. However, it should also work with other models and also the extension module *EM 4 top2*. 

[0]: http://www.theben.de/en/Products/TIME/Digital-time-switches/DIN-rail/Yearly-program/Yearly-program "Theben product page"