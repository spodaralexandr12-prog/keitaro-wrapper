
import os
import secrets
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

from keitaro import KeitaroAPI

load_dotenv()

# DATABASE

engine = create_engine(
    "sqlite:///./keitaro_wrapper.db",
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    keitaro_id = Column(Integer, unique=True, nullable=False)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    offer_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)



# APPLICATION

app = FastAPI(title="Keitaro Wrapper")
api = KeitaroAPI()


# REQUEST MODELS

class CreateCampaign(BaseModel):
    name: str = Field(min_length=1)
    country: str = Field(min_length=2, max_length=2)
    offer_id: int = Field(gt=0)


class UpdateOffer(BaseModel):
    stream_id: int
    offer_id: int = Field(gt=0)
    action: str


# HELPERS

def get_streams(campaign_id):
    return api.get(f"campaigns/{campaign_id}/streams")


def stream_payload(stream, offers=None):
    return {
        "campaign_id": stream["campaign_id"],
        "type": stream["type"],
        "name": stream["name"],
        "schema": stream["schema"],
        "action_type": stream["action_type"],
        "action_payload": stream.get("action_payload") or "",
        "filters": [
            {
                "name": item["name"],
                "mode": item["mode"],
                "payload": item["payload"]
            }
            for item in stream.get("filters", [])
        ],
        "weight": stream.get("weight", 100),
        "offer_selection": stream.get("offer_selection", "before_click"),
        "position": stream.get("position", 1),
        "state": stream.get("state", "active"),
        "offers": offers if offers is not None else [
            {
                "offer_id": item["offer_id"],
                "share": item.get("share", 100),
                "state": item.get("state", "active")
            }
            for item in stream.get("offers", [])
        ],
        "landings": [],
        "triggers": stream.get("triggers", [])
    }


# FRONTEND

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Keitaro Wrapper</title>
        <style>
            body {
                font-family: Arial;
                max-width: 750px;
                margin: 40px auto;
                padding: 20px;
                background: #f4f4f4;
            }
            section {
                background: white;
                padding: 20px;
                margin-bottom: 20px;
                border-radius: 8px;
            }
            input, button, select {
                display: block;
                width: 100%;
                box-sizing: border-box;
                padding: 10px;
                margin: 10px 0;
            }
            button {
                cursor: pointer;
                background: #222;
                color: white;
                border: none;
            }
            pre {
                white-space: pre-wrap;
                overflow-wrap: anywhere;
            }
        </style>
    </head>
    <body>
        <h1>Keitaro Wrapper</h1>

        <section>
            <h2>Создание кампании</h2>
            <input id="name" placeholder="Название кампании">
            <input id="country" placeholder="GEO-код, например KZ">
            <input id="offer" type="number" placeholder="ID оффера">
            <button onclick="createCampaign()">Создать кампанию</button>
            <pre id="createResult"></pre>
        </section>

        <section>
            <h2>Редактирование офферов</h2>
            <input id="campaignId" type="number" placeholder="ID кампании">
            <input id="streamId" type="number" placeholder="ID потока">
            <input id="editOffer" type="number" placeholder="ID оффера">
            <select id="action">
                <option value="add">Добавить оффер</option>
                <option value="remove">Удалить оффер</option>
            </select>
            <button onclick="updateOffer()">Изменить офферы</button>
            <pre id="editResult"></pre>
        </section>

        <script>
            async function createCampaign() {
                const data = {
                    name: document.getElementById("name").value,
                    country: document.getElementById("country").value.toUpperCase(),
                    offer_id: Number(document.getElementById("offer").value)
                };

                const response = await fetch("/api/campaigns", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify(data)
                });

                document.getElementById("createResult").textContent =
                    JSON.stringify(await response.json(), null, 2);
            }

            async function updateOffer() {
                const campaignId = document.getElementById("campaignId").value;

                const data = {
                    stream_id: Number(document.getElementById("streamId").value),
                    offer_id: Number(document.getElementById("editOffer").value),
                    action: document.getElementById("action").value
                };

                const response = await fetch(
                    `/api/campaigns/${campaignId}/offers`,
                    {
                        method: "PUT",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify(data)
                    }
                );

                document.getElementById("editResult").textContent =
                    JSON.stringify(await response.json(), null, 2);
            }
        </script>
    </body>
    </html>
    """


# CREATE CAMPAIGN

@app.post("/api/campaigns")
def create_campaign(data: CreateCampaign):
    db = SessionLocal()

    try:
        campaign_data = {
            "name": data.name,
            "alias": secrets.token_hex(4),
            "type": "position",
            "domain_id": int(os.getenv("KEITARO_DOMAIN_ID", "1813")),
            "group_id": int(os.getenv("KEITARO_GROUP_ID", "10332")),
            "traffic_source_id": int(os.getenv("KEITARO_TRAFFIC_SOURCE_ID", "836"))
        }

        campaign = api.post("campaigns", campaign_data)
        campaign_id = campaign["id"]

        # GEO STREAM: specified country -> Google

        google_stream = {
            "campaign_id": campaign_id,
            "type": "regular",
            "name": "GOOGLE_REDIRECT",
            "schema": "redirect",
            "action_type": "http",
            "action_payload": "https://www.google.com",
            "filters": [
                {
                    "name": "country",
                    "mode": "accept",
                    "payload": [data.country]
                }
            ],
            "weight": 100
        }

        api.post("streams", google_stream)

        # DEFAULT STREAM: offer for other visitors

        offer_stream = {
            "campaign_id": campaign_id,
            "type": "default",
            "name": "OFFER_REDIRECT",
            "schema": "landings",
            "action_type": "http",
            "action_payload": "",
            "filters": [],
            "weight": 100,
            "offers": [
                {
                    "offer_id": data.offer_id,
                    "share": 100,
                    "state": "active"
                }
            ]
        }

        api.post("streams", offer_stream)

        db.add(Campaign(
            keitaro_id=campaign_id,
            name=data.name,
            country=data.country,
            offer_id=data.offer_id
        ))
        db.commit()

        return {
            "message": "Кампания и потоки созданы",
            "campaign_id": campaign_id,
            "name": data.name,
            "country": data.country,
            "offer_id": data.offer_id
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(error))

    finally:
        db.close()


# UPDATE CAMPAIGN OFFERS

@app.put("/api/campaigns/{campaign_id}/offers")
def update_offers(campaign_id: int, data: UpdateOffer):
    try:
        streams = get_streams(campaign_id)

        stream = next(
            (item for item in streams if item["id"] == data.stream_id),
            None
        )

        if stream is None:
            raise HTTPException(status_code=404, detail="Поток не найден")

        offers = [
            {
                "offer_id": item["offer_id"],
                "share": item.get("share", 100),
                "state": item.get("state", "active")
            }
            for item in stream.get("offers", [])
        ]

        if data.action == "add":
            if any(item["offer_id"] == data.offer_id for item in offers):
                raise HTTPException(
                    status_code=400,
                    detail="Оффер уже добавлен"
                )

            offers.append({
                "offer_id": data.offer_id,
                "share": 100,
                "state": "active"
            })

        elif data.action == "remove":
            offers = [
                item for item in offers
                if item["offer_id"] != data.offer_id
            ]

        else:
            raise HTTPException(
                status_code=400,
                detail="Неизвестное действие"
            )

        result = api.put(
            f"streams/{data.stream_id}",
            stream_payload(stream, offers)
        )

        return {
            "message": "Офферы обновлены",
            "stream_id": data.stream_id,
            "offers": result.get("offers", offers)
        }

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


# GET CAMPAIGNS

@app.get("/api/campaigns")
def list_campaigns():
    db = SessionLocal()

    try:
        campaigns = db.query(Campaign).all()

        return [
            {
                "id": item.id,
                "keitaro_id": item.keitaro_id,
                "name": item.name,
                "country": item.country,
                "offer_id": item.offer_id,
                "created_at": item.created_at.isoformat()
            }
            for item in campaigns
        ]

    finally:
        db.close()


@app.get("/api/campaigns/{campaign_id}/streams")
def list_streams(campaign_id: int):
    try:
        return get_streams(campaign_id)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
