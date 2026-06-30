from flask import Flask, render_template, request, Response, stream_with_context
import requests
import json
import os

app = Flask(__name__)

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL_NAME = os.environ.get("MODEL_NAME", "phi3_financial")


@app.route("/")
def index():
    return render_template("index.html", model_name=MODEL_NAME)


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    messages = data.get("messages", [])
    model = data.get("model", MODEL_NAME)

    def generate():
        try:
            resp = requests.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 512,
                    },
                },
                stream=True,
                timeout=120,
            )
            resp.raise_for_status()

            for line in resp.iter_lines():
                if line:
                    chunk = json.loads(line)
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield f"data: {json.dumps({'content': content})}\n\n"
                    if chunk.get("done"):
                        yield "data: [DONE]\n\n"
                        break

        except requests.exceptions.ConnectionError:
            msg = f"Cannot connect to Ollama ({OLLAMA_URL}). Make sure Ollama is running."
            yield f"data: {json.dumps({'error': msg})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/models")
def list_models():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        models = [m["name"] for m in r.json().get("models", [])]
        return {"status": "connected", "models": models}
    except Exception as e:
        return {"status": "disconnected", "models": [], "error": str(e)}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"TechCorp AI Chat - http://localhost:{port}")
    print(f"Ollama: {OLLAMA_URL}  |  Model: {MODEL_NAME}")
    app.run(debug=True, host="0.0.0.0", port=port)
