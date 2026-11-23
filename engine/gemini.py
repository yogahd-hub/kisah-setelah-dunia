"""Gemini API helpers: TTS (one call per video) and transcription for checking the voice over."""
import json, os, base64, urllib.request, wave

def _key():
    k = os.environ.get("GEMINI_API_KEY", "").strip()
    if not k and os.path.exists(os.path.expanduser("~/.gkey")):
        k = open(os.path.expanduser("~/.gkey")).read().strip()
    if not k:
        raise SystemExit("GEMINI_API_KEY belum di-set (GitHub: Settings > Secrets and variables > Actions)")
    return k

def _post(model, body, timeout=180):
    req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": _key()})
    return json.load(urllib.request.urlopen(req, timeout=timeout))

def tts(text, out, voice="Charon", model="gemini-3.8-flash-lite-tts", style=""):
    body = {"contents": [{"parts": [{"text": f"{style}\n{text}" if style else text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    part = _post(model, body)["candidates"][0]["content"]["parts"][0]["inlineData"]
    data = base64.b64decode(part["data"])
    if "wav" in part["mimeType"]:
        open(out, "wb").write(data); return out
    rate = int(part["mimeType"].split("rate=")[1].split(";")[0]) if "rate=" in part["mimeType"] else 24000
    with wave.open(out, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(data)
    return out

def transcribe(path, model="gemini-3.5-flash"):
    b = base64.b64encode(open(path, "rb").read()).decode()
    body = {"contents": [{"parts": [{"inlineData": {"mimeType": "audio/wav", "data": b}},
                                    {"text": "Transkripsikan PERSIS kata demi kata semua yang diucapkan di audio ini. Hanya teks."}]}]}
    return _post(model, body, timeout=120)["candidates"][0]["content"]["parts"][0]["text"].strip()
