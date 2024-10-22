# Bank Transactions

This project demonstrates how to test the Accounts and Card Accounts APIs of Handelsbanken using their Sandbox
environment.

The process goes through the following:

- Obtaining access tokens
- Authorizing requests
- Retrieving account information and transactions

## Postman

Collection and environment for Postman integration are available in the collections' folder.

### Requirements

- Python 3.12
- Valid `client_id` to enter the Handelsbanken Sandbox environment
- Internet connection

### Setup (for Windows)

- Create virtual environment

    `python -m venv venv`

- Activate virtual environment 

    `.\venv\Scripts\activate`

- Install requirements.txt

    `pip install -r requirements.txt`

- Run project

    `python main.py`
