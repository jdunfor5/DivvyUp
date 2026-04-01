# DivvyUp README
Repository for a group budgeting web-application for Spring 2026 capstone.

Test User: user@example.com
           password

## Render Deployments
Frontend: https://divvyup-static-site.onrender.com

Backend: https://divvyup-api-awun.onrender.com/

## Backend

### First-Time Setup
1. `cd backend`
3. `python -m venv venv` to create the virtual environment
4. `source venv/Scripts/activate`
5. `pip install -r requirements.txt`

**Setting Up Database** 
1. `psql -U postgres`
2. `CREATE USER divvyup_user WITH PASSWORD 'yourpassword';
CREATE DATABASE divvyup OWNER divvyup_user;
GRANT ALL PRIVILEGES ON DATABASE divvyup TO divvyup_user;
\q`
3. `copy .env.example .env` (make sure to update .env placeholders)

### General Working
1. `cd backend`
2. `source venv/Scripts/activate` (required every time you reopen your editor)
3. `pip install -r requirements.txt` (if requirements.txt has been updated)
4. Run the server: `uvicorn app.main:app --reload`

> ⚠️ Whenever you install a new package, run `pip freeze > requirements.txt` to keep dependencies up to date.
### Backend Commands
#### Dependencies
* `pip install -r requirements.txt` (install all dependencies)
* `pip install <package-name>` (install a package)
* `pip freeze > requirements.txt` (update requirements.txt with new packages)

#### Database
* `psql -U postgres` (opens PostgreSQL in terminal as superuser)
* `psql -U divvyup_user -d divvyup` (opens PostgreSQL in terminal as app user)

These next ones will be used to reset the database
* `DROP DATABASE divvyup;` 
* `CREATE DATABASE divvyup OWNER divvyup_user;`

#### Running Server
* `uvicorn app.main:app --reload`

#### Testing
* `pytest` (run all tests)
* `pytest tests/test_user.py` (run specific test file)
* `pytest -v` (verbose output)
     
## Frontend

### First-Time Setup
1. `cd frontend`
2. `npm install`
3. `npm install axios`

### General Working
1. `cd frontend`
2. `npm run dev`

> ⚠️ Whenever you install a new package, run `npm install <package-name>` and commit the updated `package.json` and `package-lock.json` to keep dependencies up to date.

# Links
Frontend
* http://localhost:5173
  
Backend
* http://127.0.0.1:8000
* http://127.0.0.1:8000/docs

PostgreSQL
* https://www.postgresql.org/download/windows/
* Set Up: https://www.youtube.com/watch?v=GpqJzWCcQXY
* Forgotten Password: https://www.youtube.com/watch?v=CHYjDuaYA4M

Node.js
* https://nodejs.org/en/download
