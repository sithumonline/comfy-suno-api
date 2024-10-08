import time
import requests
from requests.auth import _basic_auth_str
import logging


logging.basicConfig(level=logging.INFO)


class SunoGenerate:
    def __init__(self):
        pass

    make_instrumental = False
    wait_audio = True
    model = "chirp-v3-5|chirp-v3-0"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_url": ("STRING", {"default": "http://localhost:3000", "multiline": False}),
                "make_instrumental": ("BOOLEAN", {"default": cls.make_instrumental}),
                "wait_audio": ("BOOLEAN", {"default": cls.wait_audio}),
                "prompt": ("STRING", {"multiline": True}),
                "tags": ("STRING", {"multiline": False}),
                "title": ("STRING", {"multiline": False}),
                "model": ("STRING", {"default": cls.model, "multiline": False}),
            },
            "optional": {
                "username": ("STRING", {"default": "admin", "forceInput": True}),
                "password": ("STRING", {"default": "admin", "forceInput": True}),
            },
        }
    
    RETURN_TYPES = ("STRING", "STRING", "DICT")
    RETURN_NAMES = ("audio_url1", "audio_url2", "response")
    FUNCTION = "generate"

    CATEGORY = "Suno"


    def get_audio_information(self, audio_ids, base_url, username, password):
        url = f"{base_url}/api/get?ids={audio_ids}"
        headers={'Content-Type': 'application/json'}

        if username and password:
            headers['Authorization'] = _basic_auth_str(username, password)

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        return  response.json()


    def generate(self, base_url, username, password, make_instrumental, wait_audio, prompt, tags, title, model):
        if prompt is None:
            raise ValueError("Prompt is required")

        url = f"{base_url}/api/custom_generate"
        headers={'Content-Type': 'application/json'}

        if username and password:
            headers['Authorization'] = _basic_auth_str(username, password)

        payload = {
            "prompt": prompt,
            "make_instrumental": make_instrumental,
            "wait_audio": wait_audio,
            "tags": tags,
            "title": title,
            "model": model,
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"[Suno] Request failed: {e}")
            return None, None, None

        response_json = response.json()

        ids = []

        if isinstance(response_json, dict) and "id" in response_json:
            ids.append(response_json["id"])
        elif isinstance(response_json, list):
            for item in response_json:
                if "id" in item:
                    ids.append(item["id"])
                else:
                    logging.error(f"[Suno] Could not find 'id' in response {item}")
            
            if not ids:
                logging.error(f"[Suno] Could not find any ids in response {response_json}")
                return None, None, response_json
        else:
            logging.error(f"[Suno] Unexpected response format: {response_json}")
            return None, None, response_json

        logging.info(f"[Suno] Generated audio with ids: {ids}")

        for _ in range(10):
            try:
                audio_information = self.get_audio_information(",".join(ids), base_url, username, password)
                if all([audio["status"] == "streaming" for audio in audio_information]):
                    break
            except Exception as e:
                logging.error(f"[Suno] Failed to get audio information: {e}")
            time.sleep(6)
        else:
            logging.error(f"[Suno] Failed to get audio information after 10 attempts")
            return None, None, response_json

        try:
            audio_urls = [audio["audio_url"] for audio in audio_information]
        except KeyError as e:
            logging.error(f"[Suno] Missing 'audio_url' in audio information: {e}")
            return None, None, response_json

        return audio_urls[0], audio_urls[1], response_json
                        
