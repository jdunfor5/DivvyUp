from fastapi import FastAPI
from . import users, groups, expenses, comments, notifications, auth

def load_routers(app: FastAPI):
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(groups.router)
    app.include_router(expenses.router)
    app.include_router(comments.router)
    app.include_router(notifications.router)