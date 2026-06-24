# Hardware-Treiber (von Freenove)

Hierher kommen die **unveränderten** Freenove-Treiber-Dateien vom Pi-Repo.
Die HTTP-API (`api_server.py`) importiert aus diesem Ordner.

Kopiert diese Dateien aus `Freenove_Tank_Robot_Kit_for_Raspberry_Pi-main/Code/Server/`:

- `motor.py`          (Klasse `tankMotor`)
- `ultrasonic.py`     (Klasse `gpiozero_ultrasonic`)
- `infrared.py`       (Klasse `Infrared`)
- `camera.py`         (Klasse `Camera`)
- `parameter.py`      (von anderen Treibern gebraucht)
- `params.json`       (Board-Version V2.0 etc.)
- evtl. `servo.py`, `led.py` + die LED-Libs, falls ihr LED/Servo nutzt

Befehl auf dem Pi (Beispiel):
```bash
cp ~/Freenove_Tank_Robot_Kit_for_Raspberry_Pi-main/Code/Server/{motor,ultrasonic,infrared,camera,parameter}.py  pi/hardware/
cp ~/Freenove_Tank_Robot_Kit_for_Raspberry_Pi-main/Code/Server/params.json  pi/hardware/
```

> **TODO am Rover prüfen:**
> - Wie genau heißt die Lese-Methode in `infrared.py`? (im api_server.py als `read_all()` angenommen)
> - `gpiozero_ultrasonic()` ohne Argumente korrekt? (Default-Pins 27/22)
