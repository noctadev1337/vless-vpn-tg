import logging
import uuid as _uuid
import json

import aiohttp

from shared.config import XUI_HOST, XUI_PATH, XUI_USER, XUI_PASS, XUI_INBOUND_ID

log = logging.getLogger(__name__)


class XUI:
    def __init__(self, host, path, user, password, inbound_id, ssl=False):
        self.base = f"{host}{path}"
        self.user = user
        self.password = password
        self.inbound_id = inbound_id
        self.ssl = ssl

    async def _get_session(self):
        jar = aiohttp.CookieJar(unsafe=True)
        conn = aiohttp.TCPConnector(ssl=False)
        s = aiohttp.ClientSession(cookie_jar=jar, connector=conn, timeout=aiohttp.ClientTimeout(total=10))
        r = await s.post(
            f"{self.base}/login",
            data={"username": self.user, "password": self.password}
        )
        d = await r.json()
        if not d.get("success"):
            await s.close()
            raise Exception(f"XUI login failed: {self.base}")
        return s

    async def add_client(self, email, traffic_b, limit_ip, expire_ms):
        uid = str(_uuid.uuid4())
        client = {
            "id": uid, "flow": "", "email": email,
            "limitIp": limit_ip, "totalGB": traffic_b,
            "expiryTime": expire_ms, "enable": True,
            "tgId": "", "subId": "", "reset": 0,
        }
        payload = {"id": self.inbound_id, "settings": json.dumps({"clients": [client]})}
        s = await self._get_session()
        try:
            r = await s.post(f"{self.base}/panel/api/inbounds/addClient", json=payload)
            text = await r.text()
            try:
                d = json.loads(text)
            except Exception:
                raise Exception(f"addClient non-JSON: {text[:200]}")
            if d.get("success"):
                return uid
            raise Exception(f"addClient: {d}")
        finally:
            await s.close()

    async def add_client_with_uuid(self, uid, email, traffic_b, limit_ip, expire_ms):
        client = {
            "id": uid, "flow": "", "email": email,
            "limitIp": limit_ip, "totalGB": traffic_b,
            "expiryTime": expire_ms, "enable": True,
            "tgId": "", "subId": "", "reset": 0,
        }
        payload = {"id": self.inbound_id, "settings": json.dumps({"clients": [client]})}
        s = await self._get_session()
        try:
            r = await s.post(f"{self.base}/panel/api/inbounds/addClient", json=payload)
            text = await r.text()
            try:
                d = json.loads(text)
            except Exception:
                raise Exception(f"addClient non-JSON: {text[:200]}")
            if d.get("success"):
                return uid
            raise Exception(f"addClient: {d}")
        finally:
            await s.close()

    async def extend_client(
            self,
            xui_uuid: str,
            email: str,
            traffic_b: int,
            limit_ip: int,
            new_exp_ms: int,
    ):
        """Обновляет срок, лимит трафика и лимит устройств существующего клиента
        без изменения его UUID (ключ у пользователя остаётся тем же)."""
        client = {
            "id": xui_uuid,
            "flow": "",
            "email": email,
            "limitIp": limit_ip,
            "totalGB": traffic_b,
            "expiryTime": new_exp_ms,
            "enable": True,
            "tgId": "",
            "subId": "",
            "reset": 0,
        }
        payload = {"id": self.inbound_id, "settings": json.dumps({"clients": [client]})}
        s = await self._get_session()
        try:
            r = await s.post(
                f"{self.base}/panel/api/inbounds/updateClient/{xui_uuid}",
                json=payload,
            )
            text = await r.text()
            try:
                d = json.loads(text)
            except Exception:
                raise Exception(f"updateClient non-JSON: {text[:200]}")
            if d.get("success"):
                return True
            raise Exception(f"updateClient: {d}")
        finally:
            await s.close()

    async def get_traffic(self, email):
        try:
            s = await self._get_session()
            try:
                r = await s.get(f"{self.base}/panel/api/inbounds/getClientTraffics/{email}")
                d = json.loads(await r.text())
                if d.get("success"):
                    return d.get("obj") or {}
            finally:
                await s.close()
        except Exception as e:
            log.error(f"XUI traffic: {e}")
        return {}

    async def get_connected_ips(self, email: str) -> int:
        try:
            s = await self._get_session()
            try:
                r = await s.get(f"{self.base}/panel/api/inbounds/clientIps/{email}")
                d = json.loads(await r.text())
                if d.get("success") and d.get("obj"):
                    ips = [ip for ip in d["obj"].split(",") if ip.strip()]
                    return len(ips)
            finally:
                await s.close()
        except Exception as e:
            log.error(f"XUI clientIps: {e}")
        return 0

    async def delete_client(self, xui_uuid):
        try:
            s = await self._get_session()
            try:
                r = await s.post(
                    f"{self.base}/panel/api/inbounds/{self.inbound_id}/delClient/{xui_uuid}"
                )
                d = json.loads(await r.text())
                return d.get("success", False)
            finally:
                await s.close()
        except Exception as e:
            log.error(f"XUI delete: {e}")
            return False


xui = XUI(XUI_HOST, XUI_PATH, XUI_USER, XUI_PASS, XUI_INBOUND_ID)
xui_ws = XUI(XUI_HOST, XUI_PATH, XUI_USER, XUI_PASS, 2)

_xui2 = None


def get_xui2():
    global _xui2
    if _xui2 is None:
        from api.config import XUI2_HOST, XUI2_PATH, XUI2_USER, XUI2_PASS, XUI2_INBOUND_ID
        _xui2 = XUI(XUI2_HOST, XUI2_PATH, XUI2_USER, XUI2_PASS, XUI2_INBOUND_ID)
    return _xui2


_xui2_ws = None


def get_xui2_ws():
    global _xui2_ws
    if _xui2_ws is None:
        from api.config import XUI2_HOST, XUI2_PATH, XUI2_USER, XUI2_PASS, XUI2_WS_INBOUND_ID
        _xui2_ws = XUI(XUI2_HOST, XUI2_PATH, XUI2_USER, XUI2_PASS, XUI2_WS_INBOUND_ID)
    return _xui2_ws


xui3 = XUI(XUI_HOST, XUI_PATH, XUI_USER, XUI_PASS, 3)


def get_xui3_de():
    from api.config import XUI2_HOST, XUI2_PATH, XUI2_USER, XUI2_PASS
    return XUI(XUI2_HOST, XUI2_PATH, XUI2_USER, XUI2_PASS, 3)
