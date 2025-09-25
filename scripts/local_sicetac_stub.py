from fastapi import FastAPI, Response, Request

SAMPLE_XML = """<?xml version='1.0' encoding='ISO-8859-1' ?>
<root>
  <documento>
    <ruta>106</ruta>
    <nombreunidadtransporte>TERMOKING</nombreunidadtransporte>
    <nombretipocarga>Carga Refrigerada</nombretipocarga>
    <nombreruta>BOGOTA _ MEDELLIN</nombreruta>
    <valor>2693308.96</valor>
    <valortonelada>79214.97</valortonelada>
    <valorhora>55118</valorhora>
    <distancia>416</distancia>
  </documento>
  <documento>
    <ruta>106</ruta>
    <nombreunidadtransporte>ESTACAS</nombreunidadtransporte>
    <nombretipocarga>General</nombretipocarga>
    <nombreruta>BOGOTA _ MEDELLIN</nombreruta>
    <valor>2478949.67</valor>
    <valortonelada>72910.28</valortonelada>
    <valorhora>37926.89</valorhora>
    <distancia>416</distancia>
  </documento>
</root>
""".strip()

app = FastAPI()

@app.post("/ws/rndcService")
async def sicetac_mock(_: Request) -> Response:
    return Response(content=SAMPLE_XML, media_type="text/xml; charset=ISO-8859-1")
