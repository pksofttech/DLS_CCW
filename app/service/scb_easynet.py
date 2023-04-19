# encoding=utf-8
from bs4 import BeautifulSoup
import httpx as requests
from pydantic import BaseModel
from ..stdio import *

Header = {
    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en,th;q=0.9,th-TH;q=0.8",
    "Host": "www.scbeasy.com",
    "Origin": "https://www.scbeasy.com",
    "Referer": "https://www.scbeasy.com/online/easynet/page/cust_csent_xsell.aspx",
    "sec-ch-ua": '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
}


def sign_in(BANK):
    print_warning("Sing_in")
    url = "https://www.scbeasy.com/online/easynet/page/lgn/login.aspx"
    headers = Header
    form_data = {
        "LOGIN": BANK["API_KEY"],
        "PASSWD": BANK["API_SECRET"],
    }
    try:
        r = requests.post(url, headers=headers, data=form_data)
        r_text = r.text
        r_lines = r_text.splitlines()
        # print(r_lines)
        SessionId = None
        for line in r_lines:
            line = line.strip()
            SESSIONEASY_KEY = 'NAME="SESSIONEASY" VALUE="'
            index = line.find(SESSIONEASY_KEY)
            if index > 0:
                index = index + len(SESSIONEASY_KEY)
                end = line.find('">', index)
                if end > 0:
                    SessionId = line[index:end]
                break

        if SessionId:
            url = "https://www.scbeasy.com/online/easynet/page/firstpage.aspx"
            headers = Header
            form_data = {
                "SESSIONEASY": SessionId,
            }
            r = requests.post(url, headers=headers, data=form_data)
            r_text = r.text
            # print(r_text)
        return SessionId
    except Exception as e:
        print_error(e)
        return ""


def get_account_balance(BANK: dict):
    # "https://www.scbeasy.com/online/easynet/page/acc/acc_bnk_bln.aspx",
    # strings.NewReader("SESSIONEASY="+scbsi.SessionId),
    # http.Header{"Content-Type": []string{"application/x-www-form-urlencoded"}})
    print_warning("get_account_balance")
    url = "https://www.scbeasy.com/online/easynet/page/acc/acc_bnk_bln.aspx"
    headers = Header
    form_data = {
        "SESSIONEASY": BANK["scb_authorize"],
    }
    print(form_data)
    try:
        r = requests.post(url, headers=headers, data=form_data)
        r.encoding = "tis_620"
        r_text = r.text
        # print(r_text)
        respond = {"success": False, "message": ""}
        if r_text.find("err_session.aspx?err_code=9") > 0:
            return respond

        bank_acc = {}
        if r_text.find("Account Balance") > 0:
            soup = BeautifulSoup(r_text, "html.parser")
            # print(soup.prettify())
            _tds = soup.find_all("td", {"class": "hd_th_blk11_bld"})
            # _tds = soup.find_all("td")
            k = None
            v = None
            for _td in _tds:
                str_td = str(_td.text).strip()
                # print_warning(str_td)
                if not k:
                    k = str_td
                    continue
                if not v:
                    v = str_td
                    bank_acc[k] = v
                    k = None
                    v = None

            # print(acc)
            respond["success"] = True
            respond["data"] = bank_acc
    except Exception as e:
        return {"success": False, "message": e}
    return respond


def get_transaction(amount: int, BANK: dict):
    try:
        print_warning("get_transaction")
        url = "https://www.scbeasy.com/online/easynet/page/acc/acc_bnk_tst.aspx"
        headers = Header
        form_data = {
            "SESSIONEASY": BANK["scb_authorize"],
        }
        # print(form_data)
        r = requests.post(url, headers=headers, data=form_data)
        r.encoding = "tis_620"
        r_text = r.text
        # print(r.encoding)
        # r_text = r_text.decode("utf-8")
        respond = {"success": False, "message": ""}
        if r_text.find("err_session.aspx?err_code=9") > 0:
            print(r_text)
            return respond

        transaction = {}
        tr_key = ["Date", "Time", "Transaction", "Channel", "Withdrawal", "Deposits", "Description"]
        if r_text.find("Statement - Today") > 0:
            soup = BeautifulSoup(r_text, "html.parser")
            # print(soup.prettify())
            _tds = soup.find_all("td", {"class": "bd_th_blk11_rtlt10_tpbt5"})
            # _tds = soup.find_all("td")
            index_key = 0
            if len(_tds) >= 7:

                for i, _td in enumerate(_tds):
                    str_td = str(_td.text).strip()
                    if index_key == 0:
                        if str_td.find("/") < 0:
                            continue
                    # print_warning(str_td)
                    transaction[tr_key[index_key]] = str_td
                    index_key += 1
                    if index_key >= len(tr_key):
                        index_key = 0
                        if transaction["Transaction"] == "X1":
                            break

                print(transaction)
                respond["success"] = True
                respond["data"] = transaction
            else:
                respond = {"success": False, "message": "Data not found or matches"}

    except Exception as e:
        print_error(e)
        return {"success": False, "message": e}

    # respond["success"] = True
    print_success(respond)
    return respond
