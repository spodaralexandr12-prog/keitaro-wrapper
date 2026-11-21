
import os
import requests
from dotenv import load_dotenv

load_dotenv()


KEITARO_URL = os.getenv("KEITARO_URL")
API_KEY = os.getenv("KEITARO_API_KEY")


class KeitaroAPI:

    def __init__(self):
        self.base_url = KEITARO_URL
        self.headers = {
            "Api-Key": API_KEY
        }

    def get(self, endpoint, params=None):
        url = f"{self.base_url}/admin_api/v1/{endpoint}"

        response = requests.get(
            url,
            headers=self.headers,
            params=params,
            timeout=15
        )

        response.raise_for_status()
        return response.json()

    def post(self, endpoint, data):
        url = f"{self.base_url}/admin_api/v1/{endpoint}"

        response = requests.post(
            url,
            headers=self.headers,
            json=data,
            timeout=15
        )

        if not response.ok:
            print("Ответ Keitaro:", response.text)

        response.raise_for_status()
        return response.json()

    def put(self, endpoint, data):
        url = f"{self.base_url}/admin_api/v1/{endpoint}"

        response = requests.put(
            url,
            headers=self.headers,
            json=data,
            timeout=15
        )

        response.raise_for_status()
        return response.json()

    def delete(self, endpoint):
        url = f"{self.base_url}/admin_api/v1/{endpoint}"

        response = requests.delete(
            url,
            headers=self.headers,
            timeout=15
        )

        response.raise_for_status()

        if response.content:
            return response.json()

        return None
