import requests

BASE_URL = "http://wheely.local:8080"

def move(direction, speed=1200, duration_ms=1000):
    payload = {
        "direction": direction,
        "speed": speed,
        "duration_ms": duration_ms
    }

    response = requests.post(
        f"{BASE_URL}/move",
        json=payload,
        timeout=5
    )

    response.raise_for_status()
    return response.json()


while True:
    command = input("Was soll der Roboter tun? ")

    if command == "stop":
        print("Programm beendet.")
        break

    if command == "vor":
        result = move("forward")

    elif command == "zurück":
        result = move("backward")

    elif command == "links":
        result = move("left")

    elif command == "rechts":
        result = move("right")

    else:
        print("Befehl nicht erkannt. Nutze: vor, zurück, links, rechts oder stop")
        continue

    print(result)