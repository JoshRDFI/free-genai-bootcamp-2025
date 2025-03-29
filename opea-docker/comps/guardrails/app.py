from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

@app.middleware("http")
async def guardrails_middleware(request: Request, call_next):
    # Implement input filtering or modifications here
    print(f"Guardrails received request: {request.url}")
    response = await call_next(request)
    # Optionally, apply output filtering here
    return response

@app.get("/health")
async def health_check():
    return {"status": "guardrails healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9400)