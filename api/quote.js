const SICETAC_ENDPOINT = process.env.SICETAC_ENDPOINT || 'http://rndcws.mintransporte.gov.co:8080/ws/rndcService';
const SICETAC_USERNAME = process.env.SICETAC_USERNAME || '';
const SICETAC_PASSWORD = process.env.SICETAC_PASSWORD || '';
const SICETAC_TIMEOUT_MS = (Number(process.env.SICETAC_TIMEOUT_SECONDS || '30') || 30) * 1000;

const DEFAULT_VARIABLES = [
  'RUTA',
  'NOMBREUNIDADTRANSPORTE',
  'NOMBRETIPOCARGA',
  'NOMBRERUTA',
  'VALOR',
  'VALORTONELADA',
  'VALORHORA',
  'DISTANCIA'
];

function toFloat(value) {
  if (value === undefined || value === null || value === '') {
    return null;
  }
  const sanitized = String(value).replace(/[',]/g, '.');
  const parsed = Number(sanitized);
  return Number.isFinite(parsed) ? parsed : null;
}

function sanitizeVariables(vars) {
  if (!Array.isArray(vars) || vars.length === 0) {
    return DEFAULT_VARIABLES;
  }
  return vars
    .map((item) => String(item || '').trim())
    .filter(Boolean)
    .map((item) => item.toUpperCase());
}

function buildDocumentSection(request) {
  const parts = [
    `<PERIODO>'${request.period}'</PERIODO>`,
    `<CONFIGURACION>'${request.configuration}'</CONFIGURACION>`,
    `<ORIGEN>'${request.origin}'</ORIGEN>`,
    `<DESTINO>'${request.destination}'</DESTINO>`
  ];

  if (request.unit_type) {
    parts.push(`<NOMBREUNIDADTRANSPORTE>'${request.unit_type.toUpperCase()}'</NOMBREUNIDADTRANSPORTE>`);
  }

  if (request.cargo_type) {
    parts.push(`<NOMBRETIPOCARGA>'${request.cargo_type.toUpperCase()}'</NOMBRETIPOCARGA>`);
  }

  return parts.join('\n    ');
}

function buildPayload(request) {
  const variables = sanitizeVariables(request.variables);
  const documentSection = buildDocumentSection(request);

  return `<?xml version='1.0' encoding='ISO-8859-1' ?>
<root>
  <acceso>
    <username>${SICETAC_USERNAME}</username>
    <password>${SICETAC_PASSWORD}</password>
  </acceso>
  <solicitud>
    <tipo>2</tipo>
    <procesoid>26</procesoid>
  </solicitud>
  <variables>
    ${variables.join(', ')}
  </variables>
  <documento>
    ${documentSection}
  </documento>
</root>`;
}

async function readJsonBody(req) {
  return new Promise((resolve, reject) => {
    let raw = '';
    req.on('data', (chunk) => {
      raw += chunk;
      if (raw.length > 2 * 1024 * 1024) {
        reject(new Error('Request body too large'));
      }
    });
    req.on('end', () => {
      if (!raw) {
        resolve({});
        return;
      }
      try {
        resolve(JSON.parse(raw));
      } catch (error) {
        reject(new Error('Invalid JSON body'));
      }
    });
    req.on('error', reject);
  });
}

function validateRequest(body) {
  const requiredFields = ['period', 'configuration', 'origin', 'destination'];
  for (const field of requiredFields) {
    if (!body[field]) {
      throw new Error(`Missing required field: ${field}`);
    }
  }

  return {
    period: String(body.period).trim(),
    configuration: String(body.configuration).trim(),
    origin: String(body.origin).trim(),
    destination: String(body.destination).trim(),
    cargo_type: body.cargo_type ? String(body.cargo_type).trim() : null,
    unit_type: body.unit_type ? String(body.unit_type).trim() : null,
    variables: Array.isArray(body.variables) ? body.variables : null,
    logistics_hours: Number(body.logistics_hours ?? 0) || 0
  };
}

async function callSicetac(payload) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), SICETAC_TIMEOUT_MS);

  try {
    const response = await fetch(SICETAC_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'text/xml; charset=ISO-8859-1'
      },
      body: Buffer.from(payload, 'latin1'),
      signal: controller.signal
    });

    const text = await response.text();

    if (!response.ok) {
      throw new Error(`Sicetac responded with status ${response.status}: ${text.slice(0, 200)}`);
    }

    return text;
  } finally {
    clearTimeout(timeout);
  }
}

function extractTagValue(fragment, tagName) {
  const regex = new RegExp(`<${tagName}[^>]*>([\s\S]*?)<\\/${tagName}>`, 'i');
  const match = fragment.match(regex);
  if (!match) {
    return null;
  }
  return match[1].replace(/&amp;/g, '&').replace(/['\s]+$/g, '').replace(/^['\s]+/g, '').trim();
}

function parseSicetacResponse(xml, request) {
  const errorMatch = xml.match(/<ErrorMSG>([\s\S]*?)<\/ErrorMSG>/i);
  if (errorMatch) {
    const message = errorMatch[1].trim();
    throw new Error(message || 'Sicetac reported an error');
  }

  const documentPattern = /<documento>([\s\S]*?)<\/documento>/gi;
  const documents = [];
  let docMatch;

  while ((docMatch = documentPattern.exec(xml)) !== null) {
    documents.push(docMatch[1]);
  }

  if (documents.length === 0) {
    throw new Error('Sicetac response did not include any quotes');
  }

  const results = [];
  for (const fragment of documents) {
    const mobilization = toFloat(extractTagValue(fragment, 'VALOR'));
    if (mobilization == null) {
      continue;
    }

    const hourValue = toFloat(extractTagValue(fragment, 'VALORHORA'));
    const minimum = hourValue != null ? mobilization + hourValue * request.logistics_hours : mobilization;

    results.push({
      route_code: extractTagValue(fragment, 'RUTA'),
      route_name: extractTagValue(fragment, 'NOMBRERUTA'),
      unit_type: extractTagValue(fragment, 'NOMBREUNIDADTRANSPORTE'),
      cargo_type: extractTagValue(fragment, 'NOMBRETIPOCARGA'),
      mobilization_value: mobilization,
      ton_value: toFloat(extractTagValue(fragment, 'VALORTONELADA')),
      hour_value: hourValue,
      distance_km: toFloat(extractTagValue(fragment, 'DISTANCIA')),
      minimum_payable: minimum
    });
  }

  if (results.length === 0) {
    throw new Error('Sicetac did not return monetary values for the requested parameters');
  }

  return results;
}

function sanitizeCredentials() {
  if (!SICETAC_USERNAME || !SICETAC_PASSWORD) {
    throw new Error('Sicetac credentials are not set in the environment');
  }
}

module.exports = async function handler(req, res) {
  if (req.method === 'OPTIONS') {
    res.status(204).end();
    return;
  }

  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method Not Allowed' });
    return;
  }

  try {
    sanitizeCredentials();
    const body = await readJsonBody(req);
    const request = validateRequest(body);

    const payload = buildPayload(request);

    let attempt = 0;
    let responseText = '';
    let lastError = null;

    while (attempt < 3) {
      attempt += 1;
      try {
        responseText = await callSicetac(payload);
        break;
      } catch (error) {
        lastError = error;
        if (attempt >= 3) {
          throw error;
        }
      }
    }

    const quotes = parseSicetacResponse(responseText, request);

    res.status(200).json({
      request,
      quotes
    });
  } catch (error) {
    console.error('[SICETAC] Request failed:', error);
    res.status(502).json({ error: error.message || 'Failed to process Sicetac quote' });
  }
};
