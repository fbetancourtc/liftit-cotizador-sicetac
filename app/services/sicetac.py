from __future__ import annotations

from dataclasses import dataclass
from typing import List

import httpx
from defusedxml import ElementTree as ET
from fastapi import HTTPException, status
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import Settings, get_settings
from app.models.quotes import QuoteRequest, QuoteResult

_DEFAULT_VARIABLES = [
    "RUTA",
    "NOMBREUNIDADTRANSPORTE",
    "NOMBRETIPOCARGA",
    "NOMBRERUTA",
    "VALOR",
    "VALORTONELADA",
    "VALORHORA",
    "DISTANCIA",
]


def _retry_request(func):
    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)

    return wrapper


def _to_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


@dataclass
class SicetacClient:
    settings: Settings

    async def fetch_quotes(self, quote_request: QuoteRequest) -> List[QuoteResult]:
        payload = self._build_payload(quote_request)
        response_text = await self._post_payload(payload)
        return self._parse_response(response_text, quote_request)

    def _build_payload(self, quote_request: QuoteRequest) -> str:
        variables = quote_request.variables or _DEFAULT_VARIABLES
        variable_string = ", ".join(variables)
        document_lines = [
            f"<PERIODO>'{quote_request.period}'</PERIODO>",
            f"<CONFIGURACION>'{quote_request.configuration}'</CONFIGURACION>",
            f"<ORIGEN>'{quote_request.origin}'</ORIGEN>",
            f"<DESTINO>'{quote_request.destination}'</DESTINO>",
        ]
        if quote_request.unit_type:
            document_lines.append(
                f"<NOMBREUNIDADTRANSPORTE>'{quote_request.unit_type.upper()}'</NOMBREUNIDADTRANSPORTE>"
            )
        if quote_request.cargo_type:
            document_lines.append(
                f"<NOMBRETIPOCARGA>'{quote_request.cargo_type.upper()}'</NOMBRETIPOCARGA>"
            )

        document_section = "\n    ".join(document_lines)
        payload = f"""<?xml version='1.0' encoding='ISO-8859-1' ?>
<root>
  <acceso>
    <username>{self.settings.sicetac_username}</username>
    <password>{self.settings.sicetac_password}</password>
  </acceso>
  <solicitud>
    <tipo>2</tipo>
    <procesoid>26</procesoid>
  </solicitud>
  <variables>
    {variable_string}
  </variables>
  <documento>
    {document_section}
  </documento>
</root>
"""
        return payload

    @_retry_request
    async def _post_payload(self, payload: str) -> str:
        headers = {"Content-Type": "text/xml; charset=ISO-8859-1"}
        async with httpx.AsyncClient(verify=self.settings.sicetac_verify_ssl) as client:
            response = await client.post(
                self.settings.sicetac_endpoint,
                content=payload.encode("iso-8859-1"),
                headers=headers,
                timeout=self.settings.sicetac_timeout_seconds,
            )
            response.raise_for_status()
            return response.text

    def _parse_response(self, response_text: str, quote_request: QuoteRequest) -> List[QuoteResult]:
        try:
            root = ET.fromstring(response_text)
        except ET.ParseError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to parse response from Sicetac",
            ) from exc

        error_node = root.find("ErrorMSG")
        if error_node is not None and error_node.text:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_node.text.strip())

        documents = root.findall("documento")
        if not documents:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sicetac response did not include any quotes",
            )

        results: List[QuoteResult] = []
        for document in documents:
            values = {child.tag.lower(): (child.text or "").strip() for child in document}
            mobilization_text = values.get("valor")
            if mobilization_text in (None, ""):
                continue
            mobilization = _to_float(mobilization_text)
            if mobilization is None:
                continue
            hour_value = _to_float(values.get("valorhora"))
            minimum_payable = mobilization
            if hour_value is not None:
                minimum_payable += hour_value * quote_request.logistics_hours
            results.append(
                QuoteResult(
                    route_code=values.get("ruta"),
                    route_name=values.get("nombreruta"),
                    unit_type=values.get("nombreunidadtransporte"),
                    cargo_type=values.get("nombretipocarga"),
                    mobilization_value=mobilization,
                    ton_value=_to_float(values.get("valortonelada")),
                    hour_value=hour_value,
                    distance_km=_to_float(values.get("distancia")),
                    minimum_payable=minimum_payable,
                )
            )
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sicetac did not return monetary values for the requested parameters",
            )
        return results


def get_sicetac_client(settings: Settings | None = None) -> SicetacClient:
    return SicetacClient(settings=settings or get_settings())
