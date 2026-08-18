Leaderboard Integration Setup

This game receives answer results from the leaderboard through a webhook.

1. Run the Game Server

Clone the repository and install the required dependencies:

git clone <repository-url>
cd <repository-folder>

pip install -r requirements.txt


Start the FastAPI server:


uvicorn main:app --host 0.0.0.0 --port 8000


The server will run on:

http://localhost:8000


2. Leaderboard Webhook

The leaderboard must send a `POST` request whenever an answer is graded.

Endpoint:

POST /webhook/leaderboard-event

Full URL:

http://<GAME_SERVER>:8000/webhook/leaderboard-event


3. Request Body

The request body must be JSON containing only the `correct` field:

{
  "correct": true
}


The corresponding FastAPI model is:

class LeaderboardEvent(BaseModel):
    correct: bool


Values

| Value   | Result                                               |
| ------- | ---------------------------------------------------- |
| `true`  | Player scored a point → Shikkari Shambhu loses 20 HP |
| `false` | Player did not score → No damage                     |


4. Example Request

Using `curl`:

curl -X POST http://localhost:8000/webhook/leaderboard-event \
  -H "Content-Type: application/json" \
  -d '{"correct": true}'


Or using Python:
import requests

response = requests.post(
    "http://localhost:8000/webhook/leaderboard-event",
    json={"correct": True}
)

print(response.status_code)

5. Response

On successful processing, the game returns:


HTTP 200 OK


No response body is required.



6. Integration Flow


Player answers question
        ↓
Leaderboard grades answer
        ↓
      Correct?
        ↓ YES
POST /webhook/leaderboard-event
        ↓
{"correct": true}
        ↓
Shikkari Shambhu takes 20 HP damage
        ↓
HTTP 200 OK


The game server handles the HP calculation and game state internally.


Initial Page:
<img width="1600" height="652" alt="image" src="https://github.com/user-attachments/assets/0d577931-d4dd-44ca-a70d-d9af1a723f85" />

When correct answer is given and when Shikkari Shambhu is above 500 hp:
<img width="1600" height="617" alt="image" src="https://github.com/user-attachments/assets/1a6a74c2-ad47-4b06-bb7e-ad718dfae102" />

When correct answer is given and when Shikkari Shambhu is below 500 hp:
<img width="1600" height="647" alt="image" src="https://github.com/user-attachments/assets/729bc5dc-fb50-4fc2-bce3-96939631c291" />

When health becomes 0:
<img width="1600" height="656" alt="image" src="https://github.com/user-attachments/assets/17f4b46c-9dcc-43df-9254-cd2bb63d1898" />

