from fastapi import FastAPI, Depends
from secure_vault.core.config import get_settings
from secure_vault.api import auth, documents, messages, users
from secure_vault.core.database import init_db
import uvicorn

app = FastAPI(
    title="SecureVaultStore",
    description="Secure End-to-End Encrypted Document and Messages Management System",
    version="1.0.0"
)

# Register routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(messages.router, prefix="/api", tags=["messages"])
app.include_router(users.router, prefix="/api", tags=["users"])

@app.on_event("startup")
async def startup_event():
    await init_db()

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        workers=settings.server_workers
    )
