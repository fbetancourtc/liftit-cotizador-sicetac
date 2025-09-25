from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

import httpx
from defusedxml import ElementTree as ET
from fastapi import HTTPException, status
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import Settings, get_settings
from app.models.quotes import QuoteRequest, QuoteResult

logger = logging.getLogger(__name__)

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
        logger.debug("Starting fetch_quotes")
        payload = self._build_payload(quote_request)
        logger.debug(f"Payload built, size: {len(payload)} bytes")
        response_text = await self._post_payload(payload)
        logger.debug(f"Response received, size: {len(response_text)} bytes")
        return self._parse_response(response_text, quote_request)

    def _build_payload(self, quote_request: QuoteRequest) -> str:
        logger.debug("Building SICETAC XML payload")
        variables = quote_request.variables or _DEFAULT_VARIABLES
        variable_string = ", ".join(variables)
        logger.debug(f"Variables requested: {variable_string}")

        document_lines = [
            f"<NUMNITEMPRESATRANSPORTE>900982995</NUMNITEMPRESATRANSPORTE>",
            f"<PERIODO>{quote_request.period}</PERIODO>",
            f"<CONFIGURACION>{quote_request.configuration}</CONFIGURACION>",
            f"<ORIGEN>{quote_request.origin}</ORIGEN>",
            f"<DESTINO>{quote_request.destination}</DESTINO>",
        ]
        if quote_request.unit_type:
            logger.debug(f"Adding unit type filter: {quote_request.unit_type}")
            document_lines.append(
                f"<NOMBREUNIDADTRANSPORTE>{quote_request.unit_type.upper()}</NOMBREUNIDADTRANSPORTE>"
            )
        if quote_request.cargo_type:
            logger.debug(f"Adding cargo type filter: {quote_request.cargo_type}")
            document_lines.append(
                f"<NOMBRETIPOCARGA>{quote_request.cargo_type.upper()}</NOMBRETIPOCARGA>"
            )

        document_section = "\n    ".join(document_lines)

        # Build inner XML request
        inner_xml = f"""<?xml version='1.0' encoding='ISO-8859-1' ?>
<root>
  <acceso>
    <username>{self.settings.sicetac_username}</username>
    <password>{self.settings.sicetac_password}</password>
  </acceso>
  <solicitud>
    <tipo>1</tipo>
    <procesoid>26</procesoid>
  </solicitud>
  <variables>
    {variable_string}
  </variables>
  <documento>
    {document_section}
  </documento>
</root>"""

        # Wrap in SOAP envelope for RPC style
        payload = f"""<?xml version="1.0" encoding="ISO-8859-1"?>
<SOAP-ENV:Envelope
    xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <SOAP-ENV:Body SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
    <NS1:AtenderMensajeRNDC xmlns:NS1="urn:BPMServicesIntf-IBPMServices">
      <Request xsi:type="xsd:string">{inner_xml.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')}</Request>
    </NS1:AtenderMensajeRNDC>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""

        logger.debug(f"SOAP Envelope built, size: {len(payload)} bytes")
        return payload

    @_retry_request
    async def _post_payload(self, payload: str) -> str:
        # Use the correct SOAP endpoint
        soap_endpoint = self.settings.sicetac_endpoint.replace("/ws/rndcService", "/soap/IBPMServices")
        logger.info(f"Sending request to SICETAC SOAP endpoint: {soap_endpoint}")
        logger.debug(f"Timeout: {self.settings.sicetac_timeout_seconds}s, SSL Verify: {self.settings.sicetac_verify_ssl}")

        headers = {
            "Content-Type": "text/xml; charset=ISO-8859-1",
            "SOAPAction": "urn:BPMServicesIntf-IBPMServices#AtenderMensajeRNDC"
        }
        async with httpx.AsyncClient(verify=self.settings.sicetac_verify_ssl) as client:
            try:
                logger.debug("Sending SOAP POST request...")
                response = await client.post(
                    soap_endpoint,
                    content=payload.encode("iso-8859-1"),
                    headers=headers,
                    timeout=self.settings.sicetac_timeout_seconds,
                )
                logger.info(f"SICETAC response status: {response.status_code}")
                logger.debug(f"Response headers: {dict(response.headers)}")

                response.raise_for_status()
                response_text = response.text
                logger.debug(f"Response text (first 500 chars): {response_text[:500]}...")
                return response_text
            except httpx.TimeoutException as e:
                logger.error(f"SICETAC request timeout after {self.settings.sicetac_timeout_seconds}s: {str(e)}")
                raise
            except httpx.HTTPStatusError as e:
                logger.error(f"SICETAC HTTP error {e.response.status_code}: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error calling SICETAC: {str(e)}", exc_info=True)
                raise

    def _parse_response(self, response_text: str, quote_request: QuoteRequest) -> List[QuoteResult]:
        logger.debug("Parsing SICETAC SOAP response")
        try:
            # First parse the SOAP envelope
            soap_root = ET.fromstring(response_text)
            logger.debug(f"SOAP root tag: {soap_root.tag}")

            # Find the Body element (handling namespaces)
            body = None
            for elem in soap_root:
                if 'Body' in elem.tag:
                    body = elem
                    break

            if body is None:
                logger.error("No SOAP Body found in response")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Invalid SOAP response from SICETAC",
                )

            # Find the response element
            response_elem = None
            for elem in body:
                if 'AtenderMensajeRNDCResponse' in elem.tag:
                    response_elem = elem
                    break

            if response_elem is None:
                logger.error("No AtenderMensajeRNDCResponse found in SOAP Body")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Invalid SICETAC response structure",
                )

            # Get the actual XML content from the response
            # Try different methods to find the return element
            return_elem = None
            for elem in response_elem.iter():
                if 'return' in elem.tag.lower():
                    return_elem = elem
                    break

            if return_elem is None:
                # Try direct search without namespace
                return_elem = response_elem.find('.//return')

            if return_elem is None or return_elem.text is None:
                logger.error("No return element found in SOAP response")
                logger.debug(f"Response element structure: {[child.tag for child in response_elem]}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Empty response from SICETAC",
                )

            # The inner XML is escaped, so we need to parse it again
            inner_xml = return_elem.text
            logger.debug(f"Inner XML (first 500 chars): {inner_xml[:500]}")

            # Parse the actual SICETAC response
            root = ET.fromstring(inner_xml)
            logger.debug(f"SICETAC response root tag: {root.tag}")
        except ET.ParseError as exc:
            logger.error(f"Failed to parse XML response: {str(exc)}")
            logger.error(f"Response text was: {response_text[:1000]}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to parse response from Sicetac",
            ) from exc

        error_node = root.find("ErrorMSG")
        if error_node is not None and error_node.text:
            error_msg = error_node.text.strip()
            logger.warning(f"SICETAC returned error: {error_msg}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)

        documents = root.findall("documento")
        logger.info(f"Found {len(documents)} documents in SICETAC response")
        if not documents:
            logger.warning("No documents found in SICETAC response")
            logger.debug(f"Full response XML: {response_text}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sicetac response did not include any quotes",
            )

        results: List[QuoteResult] = []
        for idx, document in enumerate(documents):
            values = {child.tag.lower(): (child.text or "").strip() for child in document}
            logger.debug(f"Document {idx + 1} fields: {list(values.keys())}")

            mobilization_text = values.get("valor")
            if mobilization_text in (None, ""):
                logger.debug(f"Document {idx + 1}: No 'valor' field, skipping")
                continue
            mobilization = _to_float(mobilization_text)
            if mobilization is None:
                logger.debug(f"Document {idx + 1}: Invalid mobilization value '{mobilization_text}', skipping")
                continue
            logger.debug(f"Document {idx + 1}: Mobilization value = {mobilization}")
            hour_value = _to_float(values.get("valorhora"))
            minimum_payable = mobilization
            if hour_value is not None:
                minimum_payable += hour_value * quote_request.logistics_hours
            quote = QuoteResult(
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
            results.append(quote)
            logger.debug(f"Added quote {idx + 1}: Route={quote.route_code}, MinPayable={quote.minimum_payable}")

        if not results:
            logger.error("No valid quotes extracted from SICETAC response")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sicetac did not return monetary values for the requested parameters",
            )

        logger.info(f"Successfully parsed {len(results)} quotes")
        return results


def get_sicetac_client(settings: Settings | None = None) -> SicetacClient:
    return SicetacClient(settings=settings or get_settings())
