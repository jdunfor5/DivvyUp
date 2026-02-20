# DivvyUp README
Repository for a group budgeting web-application for Spring 2026 capstone.

# Render Deployments
Frontend: https://divvyup-static-site.onrender.com

Backend: https://divvyup-api-awun.onrender.com/

# Before doing anything ever
     git pull

# To set up backend
1. cd backend
    
2. (If in a bash terminal) source venv/Scripts/activate
   * You will probably have to do this step every time you re-open your editor
    
3. pip install fastapi uvicorn sqlalchemy pydantic-settings python-multipart

To run in backend directory: uvicorn app.main:app --reload

# To set up frontend
1. cd frontend
   
2. npm install
   
3. npm install axios

To run in frontend directory: npm run dev

# Links
Frontend
* http://localhost:5173
  
Backend
* http://127.0.0.1:8000
* http://127.0.0.1:8000/docs

PostgreSQL
* https://www.postgresql.org/download/windows/
* https://www.youtube.com/watch?v=GpqJzWCcQXY

Node.js
* https://nodejs.org/en/download
