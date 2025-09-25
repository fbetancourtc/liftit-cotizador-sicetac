#!/usr/bin/env python3
"""
Test SOAP SICETAC connection with proper endpoint and envelope
"""

import httpx
from app.core.config import get_settings

def test_soap_sicetac():
    """Test SOAP connection to SICETAC service"""

    settings = get_settings()

    print(f"🔑 Using credentials:")
    print(f"   Username: {settings.sicetac_username}")
    print(f"   Password: {'*' * len(settings.sicetac_password)}")

    # Build inner XML request
    inner_xml = f"""<?xml version='1.0' encoding='ISO-8859-1' ?>
<root>
  <acceso>
    <username>{settings.sicetac_username}</username>
    <password>{settings.sicetac_password}</password>
  </acceso>
  <solicitud>
    <tipo>1</tipo>
    <procesoid>26</procesoid>
  </solicitud>
  <variables>
    RUTA, NOMBREUNIDADTRANSPORTE, NOMBRETIPOCARGA, NOMBRERUTA, VALOR, VALORTONELADA, VALORHORA, DISTANCIA
  </variables>
  <documento>
    <NUMNITEMPRESATRANSPORTE>900559843-7</NUMNITEMPRESATRANSPORTE>
    <PERIODO>202501</PERIODO>
    <CONFIGURACION>3S3</CONFIGURACION>
    <ORIGEN>11001000</ORIGEN>
    <DESTINO>05001000</DESTINO>
    <NOMBREUNIDADTRANSPORTE>ESTACAS</NOMBREUNIDADTRANSPORTE>
    <NOMBRETIPOCARGA>GENERAL</NOMBRETIPOCARGA>
  </documento>
</root>"""

    # Escape the inner XML for SOAP
    escaped_xml = inner_xml.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

    # Build SOAP envelope
    soap_payload = f"""<?xml version="1.0" encoding="ISO-8859-1"?>
<SOAP-ENV:Envelope
    xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <SOAP-ENV:Body SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
    <NS1:AtenderMensajeRNDC xmlns:NS1="urn:BPMServicesIntf-IBPMServices">
      <Request xsi:type="xsd:string">{escaped_xml}</Request>
    </NS1:AtenderMensajeRNDC>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""

    # Use correct SOAP endpoint
    soap_endpoint = "http://rndcws.mintransporte.gov.co:8080/soap/IBPMServices"
    print(f"   Endpoint: {soap_endpoint}")

    print("\n📝 Sending SOAP envelope (first 500 chars):")
    print(soap_payload[:500] + "...")

    print("\n🔍 Escaped XML content:")
    print(escaped_xml[:600] + "...")

    headers = {
        "Content-Type": "text/xml; charset=ISO-8859-1",
        "SOAPAction": "urn:BPMServicesIntf-IBPMServices#AtenderMensajeRNDC"
    }

    print("\n🚀 Sending SOAP request to SICETAC...")

    try:
        with httpx.Client(verify=False) as client:
            response = client.post(
                soap_endpoint,
                content=soap_payload.encode("iso-8859-1"),
                headers=headers,
                timeout=30.0,
            )

            print(f"\n📡 Response status: {response.status_code}")
            print(f"📄 Response headers: {dict(response.headers)}")

            response_text = response.text
            print(f"\n📊 SOAP Response (first 1000 chars):")
            print(response_text[:1000])

            if len(response_text) > 1000:
                print(f"\n... (truncated, total length: {len(response_text)} chars)")

            # Try to parse SOAP response
            try:
                from defusedxml import ElementTree as ET
                soap_root = ET.fromstring(response_text)

                # Look for the Body element
                for elem in soap_root:
                    if 'Body' in elem.tag:
                        print(f"\n✅ Found SOAP Body")

                        # Look for the response
                        for body_elem in elem:
                            if 'Response' in body_elem.tag:
                                print(f"✅ Found Response element")

                                # Look for return value
                                return_elem = body_elem.find('.//return')
                                if return_elem is not None and return_elem.text:
                                    inner_response = return_elem.text
                                    print(f"\n📦 Inner XML response (first 500 chars):")
                                    print(inner_response[:500])

                                    # Parse inner XML
                                    inner_root = ET.fromstring(inner_response)

                                    # Check for error
                                    error_node = inner_root.find("ErrorMSG")
                                    if error_node is not None and error_node.text:
                                        print(f"\n❌ SICETAC Error: {error_node.text.strip()}")
                                    else:
                                        # Look for documents
                                        documents = inner_root.findall("documento")
                                        print(f"\n✅ Found {len(documents)} documents in response")

                                        for i, doc in enumerate(documents[:3], 1):  # Show first 3
                                            print(f"\nDocument {i}:")
                                            for child in doc:
                                                if child.text:
                                                    print(f"  {child.tag}: {child.text}")

            except Exception as e:
                print(f"\n❌ Failed to parse SOAP response: {e}")

    except httpx.ConnectError:
        print("❌ Could not connect to SICETAC SOAP endpoint")
    except httpx.TimeoutException:
        print("❌ Request timed out after 30 seconds")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_soap_sicetac()