from datetime import date, datetime, timedelta, timezone
import json
import os
import uuid
import requests


import base64
from PIL import Image

from ..stdio import *


DIR_PATH = os.getcwd()
# SCB
SCB_BANK = {
    "test": {
        "API_KEY": "l7866e40f81c574529b10e51d003275d62",
        "API_SECRET": "a990c428e11041fab850b9a5d61bd420",
        "AUTH_CODE": "",
        "BILLER_ID": "668523414889619",
        "MERCHANT_ID": "311643595183307",
        "ACCESS_TOKEN": "",
        "WALLET_ID": "014903958159894",
        "UUID": "",
        "REF1": "",
        "REF2": "TEST",
        "REF3": "GVU",
        "scb_authorize": "https://api-sandbox.partners.scb/partners/sandbox/v2/oauth/authorize",
        "scbGenerateAccessToken": "https://api-sandbox.partners.scb/partners/sandbox/v1/oauth/token",
        "scbQRCodeAPI": "https://api-sandbox.partners.scb/partners/sandbox/v1/payment/qrcode/create",
        "scbCheckPaySuccess": "https://api-sandbox.partners.scb/​partners/​v1/​payment/​billpayment/​inquiry",
    },
    "BUP": {
        "API_KEY": "l7740b464640b5415c9b72aa6b3e266198",
        "API_SECRET": "8fe25e7fd9414541b8a03e199388c3b6",
        "AUTH_CODE": "",
        "BILLER_ID": "010555213464788",
        "MERCHANT_ID": "xxxxxxxxx",
        "ACCESS_TOKEN": "",
        "WALLET_ID": "xxxxxxxxxx",
        "UUID": "",
        "REF1": "",
        "REF2": "DPARK",
        "REF3": "BUP",
        "scb_authorize": "",
        "scbGenerateAccessToken": "https://api.partners.scb/partners/v1/oauth/token",
        "scbQRCodeAPI": "https://api.partners.scb/partners/v1/payment/qrcode/create",
        "RequestPullSlip": "https://api.partners.scb/partners/v1/payment/billpayment/transactions",
        "scbCheckPaySuccess": "https://api.partners.scb/partners/v1/payment/billpayment/inquiry",
    },
    "MSRE": {
        "API_KEY": "l761ab0fa20fc64276aa1b00b721fc32cd",
        "API_SECRET": "7f281a9bb10f469e8adbc6a36b0eb93d",
        "AUTH_CODE": "",
        "BILLER_ID": "030555600303102",
        "MERCHANT_ID": "xxxxxxxxx",
        "ACCESS_TOKEN": "",
        "WALLET_ID": "xxxxxxxxxx",
        "UUID": "",
        "REF1": "",
        "REF2": "DPARK",
        "REF3": "MSRE",
        "scb_authorize": "",
        "scbGenerateAccessToken": "https://api.partners.scb/partners/v1/oauth/token",
        "scbQRCodeAPI": "https://api.partners.scb/partners/v1/payment/qrcode/create",
        "RequestPullSlip": "https://api.partners.scb/partners/v1/payment/billpayment/transactions",
        "scbCheckPaySuccess": "https://api.partners.scb/partners/v1/payment/billpayment/inquiry",
    },
}


def scb_authorize(BANK):
    if BANK:
        BANK["UUID"] = str(uuid.uuid4())
        UUID = BANK.get("UUID")
        API_KEY = BANK.get("API_KEY")
        API_SECRET = BANK.get("API_SECRET")
        API_KEY = BANK.get("API_KEY")

        url = BANK.get("scb_authorize")
        if url:
            headers = {
                "content-type": "application/json",
                "accept-language": "EN",
                "apikey": API_KEY,
                "apisecret": API_SECRET,
                "endState": "mobile_web",
                "requestUId": UUID,
                "resourceOwnerId": API_KEY,
                "response-channel": "mobile",
            }
            print(headers)
            r = requests.get(url, headers=headers)
            ret = r.json()
            print_success(ret)
            return ret
        else:
            return None
    return None


def scbGenerateAccessToken(BANK):
    if BANK:
        BANK["UUID"] = str(uuid.uuid4())
        UUID = BANK.get("UUID")
        API_KEY = BANK.get("API_KEY")
        API_SECRET = BANK.get("API_SECRET")
        API_KEY = BANK.get("API_KEY")
        AUTH_CODE = BANK.get("AUTH_CODE")

        url = BANK.get("scbGenerateAccessToken")
        headers = {
            "Content-type": "application/json",
            "accept-language": "EN",
            "requestUId": str(uuid.uuid4()),
            "resourceOwnerId": API_KEY,
        }

        data = {
            "applicationKey": API_KEY,
            "applicationSecret": API_SECRET,
            "authCode": AUTH_CODE,
        }
        print(url)
        print(headers)
        print(data)
        # r = requests.post(url, headers=headers, data=json.dumps(data))
        r = requests.post(url, headers=headers, data=json.dumps(data))
        print_success(r.text)
        try:
            _json = r.json()
            print(_json)
            print(_json.get("data"))
            return _json.get("data")
        except Exception as e:
            print(e)
            return None
    return None


def scbQRCodeAPI(amount: str, BANK):
    if BANK:
        # BANK["UUID"] = str(uuid.uuid4())
        UUID = BANK.get("UUID")
        API_KEY = BANK.get("API_KEY")
        BILLER_ID = BANK.get("BILLER_ID")
        API_KEY = BANK.get("API_KEY")
        WALLET_ID = BANK.get("WALLET_ID")
        ACCESS_TOKEN = BANK.get("ACCESS_TOKEN")
        REF1 = BANK.get("REF1")
        REF2 = BANK.get("REF2")
        REF3 = BANK.get("REF3")

        url = BANK.get("scbQRCodeAPI")

        headers = {
            "Content-type": "application/json",
            # "accept-language": "th",
            "requestUId": UUID,
            "resourceOwnerId": API_KEY,
            "authorization": f"Bearer {ACCESS_TOKEN}",
        }
        data = {
            "qrType": "PP",
            "amount": str(amount),
            # "invoice": "8545",
            "ppId": BILLER_ID,
            "ppType": "BILLERID",
            "ref1": REF1,
            "ref2": REF2,
            "ref3": REF3,
            # "terminalId": "265187874464964",
            # "merchantId": "414185421347988",
        }
        print(headers)
        print(data)
        r = requests.post(url, headers=headers, data=json.dumps(data))
        print_success(r.text)
        _json = r.json()
        print(_json)
        # qrRawData: str = _json.get("data").get("qrRawData")
        return _json
    return None


def scbQRCodeGeneration(amount, BANK: dict):
    if BANK:
        BANK["UUID"] = str(uuid.uuid4())

        scb_authorize(BANK)

        scb_access_token: dict = scbGenerateAccessToken(BANK)
        print_success(scb_access_token)
        if scb_access_token:
            BANK["ACCESS_TOKEN"] = scb_access_token.get("accessToken")
            _json = scbQRCodeAPI(amount, BANK)

            # print(_json)
            return _json

        return {"error": "access token not found"}


def scbCheckPaySuccess(ref01: str, BANK: dict):
    if BANK:
        BANK["UUID"] = str(uuid.uuid4())
        UUID = BANK.get("UUID")
        API_KEY = BANK.get("API_KEY")
        BILLER_ID = BANK.get("BILLER_ID")
        API_KEY = BANK.get("API_KEY")
        ACCESS_TOKEN = BANK.get("ACCESS_TOKEN")
        eventCode = "00300100"
        transactionDate = time_now().strftime("%Y-%m-%d")
        billerId = BILLER_ID
        reference1 = ref01
        reference2 = "DPARK"
        # partnerTransactionId = TransactionId

        param = f"billerId={billerId}&reference1={reference1}&reference2={reference2}&transactionDate={transactionDate}&eventCode={eventCode}"
        url = f"{BANK.get('scbCheckPaySuccess')}?{param}"

        if not ACCESS_TOKEN:
            scb_authorize(BANK)

            scb_access_token: dict = scbGenerateAccessToken(BANK)
            print_warning(scb_access_token)
            if not scb_access_token:
                return {"error": "access token not found"}
            BANK["ACCESS_TOKEN"] = scb_access_token.get("accessToken")
        headers = {
            "Content-type": "application/json",
            "accept-language": "EN",
            "requestUId": UUID,
            "resourceOwnerId": API_KEY,
            "authorization": f"Bearer {ACCESS_TOKEN}",
        }
        print(f"headers : {headers}")
        print(f"URL : {url}")
        r = requests.get(url, headers=headers)
        print_success(r.text)
        _ret = {}
        _j = r.json()
        status = _j.get("status")
        data = _j.get("data")
        if status.get("code") == 1000:
            _ret["PaymentStatus"] = "Success"
            _ret["data"] = data[0]
            return _j
        elif status.get("code") == 9500:
            print_warning("ACCESS_TOKEN ExpiresAt")
            return _j
        else:
            return _j
    return {"error": "Bank not found"}


def scbRequestPullSlip(transRef: str, BANK: dict):
    if BANK:
        BANK["UUID"] = str(uuid.uuid4())
        UUID = BANK.get("UUID")
        API_KEY = BANK.get("API_KEY")
        BILLER_ID = BANK.get("BILLER_ID")
        API_KEY = BANK.get("API_KEY")
        ACCESS_TOKEN = BANK.get("ACCESS_TOKEN")

        param = f"sendingBank=014"
        base_url = BANK.get("RequestPullSlip")
        if base_url:
            url = f"{base_url}/{transRef}?{param}"
            if not ACCESS_TOKEN:
                scb_authorize(BANK)

                scb_access_token: dict = scbGenerateAccessToken(BANK)
                print_warning(scb_access_token)
                if not scb_access_token:
                    return {"error": "access token not found"}
                BANK["ACCESS_TOKEN"] = scb_access_token.get("accessToken")
            headers = {
                "Content-type": "application/json",
                "accept-language": "EN",
                "requestUId": UUID,
                "resourceOwnerId": API_KEY,
                "authorization": f"Bearer {ACCESS_TOKEN}",
            }
            print(f"headers : {headers}")
            print(f"URL : {url}")
            r = requests.get(url, headers=headers)
            print_success(r.text)
            try:
                _j = r.json()
                return _j
            except Exception as e:
                print(e)
                return {"error": "json not found"}
        return {"error": "scbRequestPullSlip url not found"}
    return {"error": "Bank not found"}
