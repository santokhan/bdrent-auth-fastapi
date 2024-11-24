python -m venv venv

pip install -r requirements.txt

source venv/Scripts/activate # windows bash
# venv\Scripts\activate # windows powershell
# source venv/bin/activate # linux bash


uvicorn main:app --port 3005 --reload

