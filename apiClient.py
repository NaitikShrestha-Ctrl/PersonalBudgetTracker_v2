"""
api_client.py
────────────────────────────────────────────────────────────
Thin HTTP client the Tkinter GUI uses to talk to api.py.
Nothing in here touches a file or a database directly — every
method is a REST call. This is what replaces the old
load_db()/save_db() JSON functions.
────────────────────────────────────────────────────────────
"""

import requests

BASE_URL = "http://127.0.0.1:5000/api"
TIMEOUT = 5


class APIError(Exception):
    """Raised when the API is unreachable or returns an error."""
    pass


def _handle(resp):
    if resp.status_code >= 400:
        try:
            msg = resp.json().get("error") or resp.json().get("message")
        except Exception:
            msg = resp.text
        raise APIError(msg or f"HTTP {resp.status_code}")
    return resp.json()


class APIClient:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url

    def _get(self, path, **params):
        try:
            r = requests.get(f"{self.base_url}{path}", params=params, timeout=TIMEOUT)
        except requests.exceptions.RequestException as e:
            raise APIError(f"Cannot reach API server: {e}")
        return _handle(r)

    def _post(self, path, json=None):
        try:
            r = requests.post(f"{self.base_url}{path}", json=json, timeout=TIMEOUT)
        except requests.exceptions.RequestException as e:
            raise APIError(f"Cannot reach API server: {e}")
        return _handle(r)

    def _put(self, path, json=None):
        try:
            r = requests.put(f"{self.base_url}{path}", json=json, timeout=TIMEOUT)
        except requests.exceptions.RequestException as e:
            raise APIError(f"Cannot reach API server: {e}")
        return _handle(r)

    def _delete(self, path, **params):
        try:
            r = requests.delete(f"{self.base_url}{path}", params=params, timeout=TIMEOUT)
        except requests.exceptions.RequestException as e:
            raise APIError(f"Cannot reach API server: {e}")
        return _handle(r)

    # ── Auth ──────────────────────────────────────────────
    def auth(self, username, password_hash):
        return self._post("/auth", {"username": username, "password_hash": password_hash})

    # ── Expenses ──────────────────────────────────────────
    def get_expenses(self, user=None):
        return self._get("/expenses", **({"user": user} if user else {}))

    def add_expense(self, user, date, category, description, amount, note):
        return self._post("/expenses", {
            "user": user, "date": date, "category": category,
            "description": description, "amount": amount, "note": note,
        })

    def update_expense(self, eid, amount, category, description, date):
        return self._put(f"/expenses/{eid}", {
            "amount": amount, "category": category,
            "description": description, "date": date,
        })

    def delete_expense(self, eid):
        return self._delete(f"/expenses/{eid}")

    def clear_expenses(self, user):
        return self._delete("/expenses", user=user)

    # ── Category budgets ──────────────────────────────────
    def get_category_budgets(self, user=None):
        return self._get("/budgets/category", **({"user": user} if user else {}))

    def set_category_budget(self, user, category, amount):
        return self._put("/budgets/category", {"user": user, "category": category, "amount": amount})

    def delete_category_budget(self, user, category):
        return self._delete("/budgets/category", user=user, category=category)

    # ── Monthly budgets ───────────────────────────────────
    def get_monthly_budgets(self, user=None):
        return self._get("/budgets/monthly", **({"user": user} if user else {}))

    def set_monthly_budget(self, user, month, amount):
        return self._put("/budgets/monthly", {"user": user, "month": month, "amount": amount})

    def delete_monthly_budget(self, user, month):
        return self._delete("/budgets/monthly", user=user, month=month)