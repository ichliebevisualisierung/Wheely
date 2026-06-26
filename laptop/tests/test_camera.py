import requests

# Adresse deines Roboters
URL = "http://wheely.local:8080/camera"

print("Fordere Bild vom Rover an...")

response = requests.get(URL)

if response.status_code == 200:
    with open("camera_test.jpg", "wb") as f:
        f.write(response.content)

    print("✅ Bild erfolgreich gespeichert!")
    print("Datei: camera_test.jpg")
else:
    print("❌ Fehler:", response.status_code)
    print(response.text)