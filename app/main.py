from fastapi import FastAPI
from .db import Base, engine
from . import models
from .routes import router
from .middleware import MetricsMiddleware


app = FastAPI()
app.add_middleware(MetricsMiddleware)
app.include_router(router)


Base.metadata.create_all(bind=engine)
