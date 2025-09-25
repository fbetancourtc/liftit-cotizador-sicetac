#!/usr/bin/env python3
"""
Test direct SICETAC connection to debug the XML response
"""

import httpx
from app.core.config import get_settings

def test_direct_sicetac():
    """Test direct connection to SICETAC service"""

    settings = get_settings()

    print(f"🔑 Using credentials:")
    print(f"   Username: {settings.sicetac_username}")
    print(f"   Password: {'*' * len(settings.sicetac_password)}")
    print(f"   Endpoint: {settings.sicetac_endpoint}")

    # Build XML payload
    payload = f"""<?xml version='1.0' encoding='ISO-8859-1' ?>
<root>
  <acceso>
    <username>{settings.sicetac_username}</username>
    <password>{settings.sicetac_password}</password>
  </acceso>
  <solicitud>
    <tipo>2</tipo>
    <procesoid>26</procesoid>
  </solicitud>
  <variables>
    RUTA, NOMBREUNIDADTRANSPORTE, NOMBRETIPOCARGA, NOMBRERUTA, VALOR, VALORTONELADA, VALORHORA, DISTANCIA
  </variables>
  <documento>
    <PERIODO>'202501'</PERIODO>
    <CONFIGURACION>'3S3'</CONFIGURACION>
    <ORIGEN>'11001000'</ORIGEN>
    <DESTINO>'05001000'</DESTINO>
    <NOMBREUNIDADTRANSPORTE>'ESTACAS'</NOMBREUNIDADTRANSPORTE>
    <NOMBRETIPOCARGA>'GENERAL'</NOMBRETIPOCARGA>
  </documento>
</root>
"""

    print("\n📝 Sending payload:")
    print(payload[:200] + "...")

    headers = {"Content-Type": "text/xml; charset=ISO-8859-1"}

    print("\n🚀 Sending request to SICETAC...")

    try:
        with httpx.Client(verify=False) as client:
            response = client.post(
                settings.sicetac_endpoint,
                content=payload.encode("iso-8859-1"),
                headers=headers,
                timeout=30.0,
            )

            print(f"\n📡 Response status: {response.status_code}")
            print(f"📄 Response headers: {dict(response.headers)}")

            response_text = response.text
            print(f"\n📊 Response (first 1000 chars):")
            print(response_text[:1000])

            if len(response_text) > 1000:
                print(f"\n... (truncated, total length: {len(response_text)} chars)")

            # Try to parse XML
            try:
                from defusedxml import ElementTree as ET
                root = ET.fromstring(response_text)

                # Check for error
                error_node = root.find("ErrorMSG")
                if error_node is not None and error_node.text:
                    print(f"\n❌ SICETAC Error: {error_node.text.strip()}")
                else:
                    # Look for documents
                    documents = root.findall("documento")
                    print(f"\n✅ Found {len(documents)} documents in response")

                    for i, doc in enumerate(documents[:3], 1):  # Show first 3
                        print(f"\nDocument {i}:")
                        for child in doc:
                            print(f"  {child.tag}: {child.text}")

            except Exception as e:
                print(f"\n❌ Failed to parse XML: {e}")

    except httpx.ConnectError:
        print("❌ Could not connect to SICETAC endpoint")
    except httpx.TimeoutException:
        print("❌ Request timed out after 30 seconds")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_direct_sicetac()