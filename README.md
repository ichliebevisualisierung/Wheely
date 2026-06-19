

## Zum Testen einer API auf dem Server:
1. In ...Code/Server:
python robot_api.py

 2. Auf persönlichem Laptop (powershell):
Invoke-RestMethod -Method Post `
  -Uri http://wheely.local:8080/move `
  -ContentType "application/json" `
  -Body '{"direction":"backward","speed":7000,"duration_ms":3000}'

This can also be tested with Postman or another request-App.

direction can be backward, forward, left, right.

Idea:
The Robot recieves API requests with things it should do.
In a next step these requests (forward, backward, usw...) should be executed by a LLM with a prompt. This can then run on the local laptop, instead of on the RaspberryPi.



