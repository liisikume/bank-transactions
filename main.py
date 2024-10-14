from urllib.parse import parse_qs

import requests

BASE_URL = "https://sandbox.handelsbanken.com/openbanking"
TOKEN_URL = f"{BASE_URL}/oauth2/token/1.0"
CONSENT_URL = f"{BASE_URL}/psd2/v1/consents"
AUTHORIZATION_URL = f"{BASE_URL}/oauth2/authorize/1.0"
ACCOUNTS_URL = f"{BASE_URL}/psd2/v2/accounts"
transactions_url = BASE_URL + "/psd2/v2/accounts/{account_id}/transactions"

REDIRECT_URI = "https://example.com"
TPP_REQUEST_ID = "c8271b81-4229-5a1f-bf9c-758f11c1f5b1"
TPP_TRANSACTION_ID = "6b24ce42-237f-4303-a917-cf778e5013d6"
STATE_ID = "bc4b933c-bfc2-44c8-b858-eba90f559f91"
X_SANDBOX_USER = "SANDBOX-INDIVIDUAL-SE-1"
CLIENT_ID = "c5b332c413b652ec63fef491ef8acbc6"


def get_access_token(client_id: str) -> str:
    """Step 1: Request Client Credential Grant (CCG) token"""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "grant_type": "client_credentials",
        "scope": "AIS",
        "client_id": client_id,
    }

    response = requests.post(TOKEN_URL, headers=headers, data=data)

    if response.status_code == 200:
        access_token = response.json().get("access_token")
        return access_token
    else:
        raise ValueError(f"Requesting access token failed: {response.text}")


def get_consent(
        client_id: str,
        access_token: str,
        tpp_request_id: str,
        tpp_transaction_id: str
) -> str:
    """Step 2: Request consent using CCG token"""
    headers = {
        "X-IBM-Client-Id": client_id,
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Country": "SE",
        "TPP-Request-ID": tpp_request_id,
        "TPP-Transaction-ID": tpp_transaction_id,
    }

    data = {
        "access": "ALL_ACCOUNTS"
    }

    response = requests.post(CONSENT_URL, headers=headers, json=data)

    if response.status_code == 201:
        consent_id = response.json().get("consentId")
        return consent_id
    else:
        raise ValueError(f"Posting consent failed: {response.text}")


def get_consent_authorization(
        client_id: str,
        consent_id: str,
        state_id: str,
        sandbox_user: str = None
) -> str:
    """Step 3.1: Request authorization for consent"""
    headers = {
        "Accept": "application/json",
    }
    if sandbox_user:  # X-Sandbox-User is only used in sandbox environment
        headers["X-Sandbox-User"] = sandbox_user

    data = {
        "response_type": "code",
        "scope": f"AIS:{consent_id}",
        "client_id": client_id,
        "state": state_id,
        "redirect_uri": REDIRECT_URI,
    }

    response = requests.get(
        AUTHORIZATION_URL,
        headers=headers,
        params=data,
        allow_redirects=False,
    )
    if response.status_code == 302:
        location = response.headers.get("location")
        query_params = parse_qs(location)
        code = query_params.get("code")[0]
        return code
    else:
        raise ValueError(
            f"Requesting consent authorization failed: {response.text}"
        )


def get_authorization_grant_token(
        client_id: str,
        consent_id: str,
        code: str
) -> str:
    """Step 3.2: Request authorization code token for accessing accounts"""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "grant_type": "authorization_code",
        "scope": f"AIS:{consent_id}",
        "client_id": client_id,
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    response = requests.post(TOKEN_URL, headers=headers, data=data)

    if response.status_code == 200:
        access_token = response.json().get("access_token")
        return access_token
    else:
        raise ValueError(
            f"Requesting authorization grant token failed: {response.text}"
        )


def get_accounts(
        client_id: str,
        access_token: str,
        tpp_request_id: str,
        tpp_transaction_id: str
) -> list:
    """Step 4.1: Request all accounts to get account_id"""
    headers = {
        "X-IBM-Client-Id": client_id,
        "Authorization": f"Bearer {access_token}",
        "TPP-Request-ID": tpp_request_id,
        "TPP-Transaction-ID": tpp_transaction_id,
    }

    response = requests.get(ACCOUNTS_URL, headers=headers)

    if response.status_code == 200:
        return response.json().get("accounts")
    else:
        raise ValueError(f"Requesting accounts failed: {response.text}")


def get_transactions(
        client_id: str,
        access_token: str,
        tpp_request_id: str,
        tpp_transaction_id: str,
        account_id: str
) -> list:
    """Step 4.2: Request all transactions of a single account"""
    url = transactions_url.format(account_id=account_id)
    headers = {
        "X-IBM-Client-Id": client_id,
        "Authorization": f"Bearer {access_token}",
        "TPP-Request-ID": tpp_request_id,
        "TPP-Transaction-ID": tpp_transaction_id,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json().get("transactions")
    else:
        raise ValueError(f"Requesting transactions failed: {response.text}")


def main() -> None:
    """Execute main function"""

    client_access_token = get_access_token(CLIENT_ID)

    consent_id = get_consent(
        CLIENT_ID, client_access_token, TPP_TRANSACTION_ID, TPP_REQUEST_ID
    )

    state_id = STATE_ID
    code = get_consent_authorization(
        CLIENT_ID, consent_id, state_id, X_SANDBOX_USER
    )

    account_access_token = get_authorization_grant_token(
        CLIENT_ID, consent_id, code
    )

    accounts = get_accounts(
        CLIENT_ID, account_access_token, TPP_REQUEST_ID, TPP_TRANSACTION_ID
    )
    account_id = accounts[0].get("accountId")

    account_transactions = get_transactions(
        CLIENT_ID,
        account_access_token,
        TPP_REQUEST_ID,
        TPP_TRANSACTION_ID,
        account_id,
    )
    print(f"Account: {account_id}")
    for transaction in account_transactions:
        print(
            f"\t{transaction.get("amount").get("content")} "
            f"{transaction.get("amount").get("currency")} was "
            f"{transaction.get("creditDebit")} on "
            f"{transaction.get("bookingDate")}"
        )


if __name__ == "__main__":
    main()
