from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="FLOW API", version="0.1.0")

    @app.get("/api/v1/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "flow-api"}

    return app


app = create_app()
