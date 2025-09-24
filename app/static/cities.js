// Colombian cities with DIVIPOLA codes
const COLOMBIAN_CITIES = [
    // Capitals and major cities
    { name: "Bogotá D.C.", code: "11001000", department: "Cundinamarca" },
    { name: "Medellín", code: "05001000", department: "Antioquia" },
    { name: "Cali", code: "76001000", department: "Valle del Cauca" },
    { name: "Barranquilla", code: "08001000", department: "Atlántico" },
    { name: "Cartagena", code: "13001000", department: "Bolívar" },
    { name: "Cúcuta", code: "54001000", department: "Norte de Santander" },
    { name: "Bucaramanga", code: "68001000", department: "Santander" },
    { name: "Ibagué", code: "73001000", department: "Tolima" },
    { name: "Soledad", code: "08758000", department: "Atlántico" },
    { name: "Soacha", code: "25754000", department: "Cundinamarca" },
    { name: "Pereira", code: "66001000", department: "Risaralda" },
    { name: "Santa Marta", code: "47001000", department: "Magdalena" },
    { name: "Villavicencio", code: "50001000", department: "Meta" },
    { name: "Bello", code: "05088000", department: "Antioquia" },
    { name: "Valledupar", code: "20001000", department: "Cesar" },
    { name: "Pasto", code: "52001000", department: "Nariño" },
    { name: "Montería", code: "23001000", department: "Córdoba" },
    { name: "Manizales", code: "17001000", department: "Caldas" },
    { name: "Neiva", code: "41001000", department: "Huila" },
    { name: "Palmira", code: "76520000", department: "Valle del Cauca" },
    { name: "Armenia", code: "63001000", department: "Quindío" },
    { name: "Popayán", code: "19001000", department: "Cauca" },
    { name: "Sincelejo", code: "70001000", department: "Sucre" },
    { name: "Itagüí", code: "05360000", department: "Antioquia" },
    { name: "Floridablanca", code: "68276000", department: "Santander" },
    { name: "Envigado", code: "05266000", department: "Antioquia" },
    { name: "Tuluá", code: "76834000", department: "Valle del Cauca" },
    { name: "Barrancabermeja", code: "68081000", department: "Santander" },
    { name: "Dosquebradas", code: "66170000", department: "Risaralda" },
    { name: "Tunja", code: "15001000", department: "Boyacá" },
    { name: "Girón", code: "68307000", department: "Santander" },
    { name: "Apartadó", code: "05045000", department: "Antioquia" },
    { name: "Uribia", code: "44847000", department: "La Guajira" },
    { name: "Florencia", code: "18001000", department: "Caquetá" },
    { name: "Turbo", code: "05837000", department: "Antioquia" },
    { name: "Maicao", code: "44430000", department: "La Guajira" },
    { name: "Piedecuesta", code: "68547000", department: "Santander" },
    { name: "Yopal", code: "85001000", department: "Casanare" },
    { name: "Ipiales", code: "52356000", department: "Nariño" },
    { name: "Fusagasugá", code: "25290000", department: "Cundinamarca" },
    { name: "Facatativá", code: "25269000", department: "Cundinamarca" },
    { name: "Zipaquirá", code: "25899000", department: "Cundinamarca" },
    { name: "Riohacha", code: "44001000", department: "La Guajira" },
    { name: "Chía", code: "25175000", department: "Cundinamarca" },
    { name: "Magangué", code: "13430000", department: "Bolívar" },
    { name: "Quibdó", code: "27001000", department: "Chocó" },
    { name: "Cartago", code: "76147000", department: "Valle del Cauca" },
    { name: "Girardot", code: "25307000", department: "Cundinamarca" },
    { name: "Sogamoso", code: "15759000", department: "Boyacá" },
    { name: "Lorica", code: "23417000", department: "Córdoba" },
    { name: "Duitama", code: "15238000", department: "Boyacá" },
    { name: "Rionegro", code: "05615000", department: "Antioquia" },
    { name: "Ocaña", code: "54498000", department: "Norte de Santander" },
    { name: "Malambo", code: "08433000", department: "Atlántico" },
    { name: "Sabanalarga", code: "08638000", department: "Atlántico" },
    { name: "Sahagún", code: "23660000", department: "Córdoba" },
    { name: "Mosquera", code: "25473000", department: "Cundinamarca" },
    { name: "Ciénaga", code: "47189000", department: "Magdalena" },
    { name: "Cereté", code: "23162000", department: "Córdoba" },
    { name: "Aguachica", code: "20011000", department: "Cesar" },
    { name: "Guadalajara de Buga", code: "76111000", department: "Valle del Cauca" },
    { name: "Caucasia", code: "05154000", department: "Antioquia" },
    { name: "Espinal", code: "73268000", department: "Tolima" },
    { name: "Tumaco", code: "52835000", department: "Nariño" },
    { name: "Arauca", code: "81001000", department: "Arauca" },
    { name: "Yumbo", code: "76892000", department: "Valle del Cauca" },
    { name: "Leticia", code: "91001000", department: "Amazonas" },
    { name: "Puerto Carreño", code: "99001000", department: "Vichada" },
    { name: "Inírida", code: "94001000", department: "Guainía" },
    { name: "San José del Guaviare", code: "95001000", department: "Guaviare" },
    { name: "Mitú", code: "97001000", department: "Vaupés" },
    { name: "Mocoa", code: "86001000", department: "Putumayo" },
    { name: "San Andrés", code: "88001000", department: "San Andrés y Providencia" }
];

// Function to search cities
function searchCities(query) {
    const searchTerm = query.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    return COLOMBIAN_CITIES.filter(city => {
        const cityName = city.name.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
        const department = city.department.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
        return cityName.includes(searchTerm) || department.includes(searchTerm);
    });
}

// Function to get city by code
function getCityByCode(code) {
    return COLOMBIAN_CITIES.find(city => city.code === code);
}

// Function to get city by name
function getCityByName(name) {
    const searchName = name.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    return COLOMBIAN_CITIES.find(city => {
        const cityName = city.name.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
        return cityName === searchName;
    });
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { COLOMBIAN_CITIES, searchCities, getCityByCode, getCityByName };
}