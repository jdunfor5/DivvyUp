from fastapi import FastAPI
from . import users, groups, expenses, comments, notifications, auth, inspectors, categories, settlements, recurring, friendships

def load_routers(app: FastAPI):
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(groups.router)
    app.include_router(expenses.router)
    app.include_router(settlements.router)
    app.include_router(comments.router)
    app.include_router(notifications.router)
    app.include_router(categories.router)
    app.include_router(inspectors.router)
    app.include_router(recurring.router)
    app.include_router(recurring.cron_router)
    app.include_router(friendships.router)