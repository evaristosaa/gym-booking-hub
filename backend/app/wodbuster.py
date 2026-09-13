"""Read-only WodBuster client used for connection checks and live reservations.

It never calls booking or cancellation handlers. Those actions will live in the
scheduled worker, after the user has explicitly configured a target.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
}
LOGIN_URL = "https://wodbuster.com/account/login.aspx"
ROAD_TO_BOX_URL = "https://wodbuster.com/account/roadtobox.aspx"


class WodBusterError(RuntimeError):
    pass


class InvalidCredentials(WodBusterError):
    pass


class WodBusterClient:
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.logged_in = False

    def login(self) -> None:
        if self.logged_in:
            return
        try:
            initial = self.session.get(LOGIN_URL, headers=HEADERS, timeout=12)
            initial.raise_for_status()
            soup = BeautifulSoup(initial.content, "html.parser")
            viewstate = soup.find(id="__VIEWSTATEC")["value"]
            validation = soup.find(id="__EVENTVALIDATION")["value"]
            csrf = soup.find(id="CSRFToken")["value"]
            response = self._login_request(viewstate, validation, csrf, {
                "ctl00$ctl00$body$ctl00": "ctl00$ctl00$body$ctl00|ctl00$ctl00$body$body$CtlLogin$CtlAceptar",
                "ctl00$ctl00$body$body$CtlLogin$IoTri": "",
                "ctl00$ctl00$body$body$CtlLogin$IoTrg": "",
                "ctl00$ctl00$body$body$CtlLogin$IoTra": "",
                "ctl00$ctl00$body$body$CtlLogin$IoEmail": self.username,
                "ctl00$ctl00$body$body$CtlLogin$IoPassword": self.password,
                "ctl00$ctl00$body$body$CtlLogin$cIoUid": "",
                "ctl00$ctl00$body$body$CtlLogin$CtlAceptar": "Aceptar\n",
            })
            if 'class="Warning"' in response.text:
                raise InvalidCredentials("Usuario o contraseña de WodBuster incorrectos")
            confirm_viewstate = self._delimited_value(response.text, "__VIEWSTATEC")
            confirm_validation = self._delimited_value(response.text, "__EVENTVALIDATION")
            self._login_request(confirm_viewstate, confirm_validation, csrf, {
                "ctl00$ctl00$body$ctl00": "ctl00$ctl00$body$ctl00|ctl00$ctl00$body$body$CtlConfiar$CtlSeguro",
                "ctl00$ctl00$body$body$CtlConfiar$dispositivo": "CtlSeguro",
            })
            self.logged_in = True
        except InvalidCredentials:
            raise
        except (KeyError, TypeError, ValueError, requests.RequestException) as exc:
            raise WodBusterError("WodBuster no respondió como se esperaba") from exc

    def _login_request(self, viewstate: str, validation: str, csrf: str, extra: dict[str, str]):
        payload = {
            "CSRFToken": csrf, "__EVENTTARGET": "", "__EVENTARGUMENT": "", "__VIEWSTATEC": viewstate,
            "__VIEWSTATE": "", "__EVENTVALIDATION": validation, "__ASYNCPOST": "true", **extra,
        }
        response = self.session.post(LOGIN_URL, data=payload, headers=HEADERS, timeout=12)
        response.raise_for_status()
        return response

    @staticmethod
    def _delimited_value(text: str, field: str) -> str:
        start = text.index(field) + len(field) + 1
        return text[start:].split("|")[0]

    def box_url(self) -> str:
        self.login()
        try:
            response = self.session.get(ROAD_TO_BOX_URL, headers=HEADERS, allow_redirects=False, timeout=12)
            location = response.headers.get("Location", "")
            if "login" in location:
                raise InvalidCredentials("Sesión de WodBuster rechazada")
            if "/user" not in location:
                raise WodBusterError("No se pudo determinar el box de WodBuster")
            return location.split("/user", 1)[0]
        except (InvalidCredentials, WodBusterError):
            raise
        except requests.RequestException as exc:
            raise WodBusterError("No se pudo consultar tu box") from exc

    def future_confirmed_reservations(self, box_url: str, days: int = 21) -> list[dict[str, str]]:
        self.login()
        today = datetime.now(timezone.utc).date()
        reservations: list[dict[str, str]] = []
        for offset in range(days + 1):
            class_date = today + timedelta(days=offset)
            epoch = int(datetime.combine(class_date, datetime.min.time(), tzinfo=timezone.utc).timestamp())
            try:
                response = self.session.get(f"{box_url}/athlete/handlers/LoadClass.ashx?ticks={epoch}", headers=HEADERS, timeout=12)
                response.raise_for_status()
                payload = response.json()
            except (ValueError, requests.RequestException) as exc:
                raise WodBusterError("No se pudieron leer las reservas de WodBuster") from exc
            for item in payload.get("Data", []):
                values = item.get("Valores") or [{}]
                if values[0].get("TipoEstado") != "Borrable":
                    continue
                details = values[0].get("Valor") or {}
                reservations.append({
                    "date": class_date.isoformat(),
                    "time": item.get("Hora", "")[:5],
                    "name": str(details.get("Nombre") or details.get("Actividad") or "Clase"),
                })
        return reservations

    def book(self, box_url: str, class_date: date, class_time: str) -> str:
        """Book one configured class. Returns `booked` or `already_booked`."""
        self.login()
        epoch = int(datetime.combine(class_date, datetime.min.time(), tzinfo=timezone.utc).timestamp())
        try:
            response = self.session.get(f"{box_url}/athlete/handlers/LoadClass.ashx?ticks={epoch}", headers=HEADERS, timeout=12)
            response.raise_for_status()
            payload = response.json()
            target = next((item for item in payload.get("Data", []) if item.get("Hora", "")[:5] == class_time), None)
            if not target:
                raise WodBusterError("No existe esa clase en el calendario")
            state = (target.get("Valores") or [{}])[0]
            if state.get("TipoEstado") == "Borrable":
                return "already_booked"
            details = state.get("Valor") or {}
            if len(details.get("AtletasEntrenando") or []) >= int(details.get("Plazas") or 0):
                raise WodBusterError("La clase está completa")
            booking_id = details.get("Id")
            if not booking_id:
                raise WodBusterError("WodBuster no devolvió el identificador de la clase")
            booked = self.session.get(f"{box_url}/athlete/handlers/Calendario_Inscribir.ashx?id={booking_id}&ticks={epoch}", headers=HEADERS, timeout=12)
            booked.raise_for_status()
            if not booked.json().get("Res", {}).get("EsCorrecto"):
                raise WodBusterError("WodBuster rechazó la reserva")
            return "booked"
        except WodBusterError:
            raise
        except (ValueError, requests.RequestException) as exc:
            raise WodBusterError("No se pudo completar la reserva en WodBuster") from exc
