"""Serveur FastAPI pour SOS Routier."""

import json

import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from pipeline import list_audio_files, run_pipeline

app = FastAPI(title="SOS Routier")


@app.get("/api/files")
def get_files():
    """Liste les fichiers audio disponibles."""
    return {"files": list_audio_files()}


@app.get("/api/run/{filename}")
def run(filename: str):
    """Lance le pipeline et stream les résultats via SSE."""

    def event_stream():
        for event in run_pipeline(filename):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        yield 'data: {"step": "done", "status": "done"}\n\n'

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# Servir les fichiers statiques (frontend)
app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
