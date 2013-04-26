# -*- coding: utf-8 -*-
"""Config value(s) for lantop client API and CLI"""

# where settings for the CLI are stored (only the default IP so far)
LANTOP_CONF_PATH = '~/.config/lantop/'


############################################################
# The following are rather consts than configurable values
# Change the Labels freely, but keep the lengths the same
############################################################

# Label and number of channels of possible devices (index by their id)
DEVICE_TYPES = {0x06: ("TR 641 top2 RC", 1),
                0x07: ("TR 642 top2 RC", 2),
                0x08: ("TR 644 top2 RC", 4),
                0x20: ("TR 641 top2", 1),
                0x21: ("TR 642 top2", 2),
                0x22: ("TR 644 top2", 4)}

# Labels for the reasons a channel is on/off
STATE_REASONS = ("Auto", "Auto", "Auto", "Zufall 2", "Zufall 1", "Impuls",
                 "Zyklus", "Hand", "Treppe ext", "Timer int", "Timer ext",
                 "Ferien", "Dauer int", "Dauer int", "Dauer ext",
                 "Dauer ext", "Signal", "Sonder 1", "Sonder 2", "Sonder 3",
                 "Sonder 4", "Sonder 5", "Sonder 6", "Sonder 7", "Sonder 8",
                 "Sonder 9", "Sonder 10", "Sonder 11", "Sonder 12",
                 "Sonder 13", "Sonder 14", "Service")

# Map the possible channel control modes (states) to their commend code
CONTROL_MODES = {'on': 2, 'off': 1, 'auto': 3, 'manual': 0}

# For timed state changed only on and off are available
TIMED_STATE_LABELS = {'on': 1, 'off': 0}

# Labels for the error codes returned by the device
ERROR_NAMES = (" ", "UHR NICHT BEREIT", "UNGUELTIGER BEFEHL", "ADRESS-FEHLER",
               "UHR PASST NICHT ZUR DATEI", "EEPROM-FEHLER",
               "FALSCHER PARAMETER", "TIMEOUT UEBERSCHRITTEN",
               "ALLGEMEINER FEHLER", "UNBEKANNT")
