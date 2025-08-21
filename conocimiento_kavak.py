# Alternativas más robustas (para producción):
# 
# RAG con embeddings + ChromaDB
# Scraping + chunking inteligente
# API de OpenAI para búsqueda semántica

"""
Base de conocimiento de Kavak para PropuestaValorTool
Organizada por secciones con keywords para búsqueda eficiente
"""

PROPUESTA_VALOR = {
    "empresa_general": {
        "keywords": ["kavak", "empresa", "que es", "quienes son", "unicornio", "mexicano", "plataforma"],
        "contenido": """Kavak México es una empresa unicornio líder en la venta de autos usados en el país, ofreciendo una experiencia única y conveniente. 

Es una plataforma de compra y venta de autos seminuevos a los mejores precios del mercado, que nació en el DF y se ha expandido a otras ciudades de la república.

Kavak llegó para reformar el mercado automotriz mexicano con ideas revolucionarias y modernas, teniendo como aliado a la tecnología para ganarse la confianza de miles de mexicanos."""
    },
    
    "sedes_ubicaciones": {
        "keywords": ["sede", "sedes", "ubicación", "ubicaciones", "donde", "direccion", "direcciones", "cdmx", "ciudad de mexico", "monterrey", "guadalajara", "puebla", "queretaro", "cuernavaca"],
        "contenido": """Kavak cuenta con 15 sedes y 13 centros de inspección cubriendo casi todo el territorio nacional.

**CIUDAD DE MÉXICO:**
• Kavak Plaza Fortuna - Av Fortuna 334, Magdalena de las Salinas
• Kavak Patio Santa Fe - Plaza Patio Santa Fe, Vasco de Quiroga 200-400
• Kavak Tlalnepantla - Perif. Blvd. Manuel Ávila Camacho 1434
• Kavak El Rosario Town Center - Av. El Rosario No. 1025
• Kavak Cosmopol - Av. José López Portillo 1, Coacalco
• Kavak Antara Fashion Hall - Av Moliere, Polanco
• Kavak Artz Pedregal - Perif. Sur 3720, Jardines del Pedregal

**MONTERREY:**
• Kavak Punto Valle - Rio Missouri 555, Del Valle, San Pedro Garza García
• Kavak Nuevo Sur - Avenida Revolución 2703, Ladrillera

**GUADALAJARA:**
• Kavak Midtown - Av López Mateos Nte 1133, Italia Providencia
• Kavak Punto Sur - Av. Punto Sur # 235, Los Gavilanes, Tlajomulco

**OTRAS CIUDADES:**
• Puebla: Kavak Explanada y Kavak Las Torres
• Querétaro: Kavak Puerta la Victoria
• Cuernavaca: Kavak Forum Cuernavaca

Horarios: Lunes a sábado 9:00 a.m. - 6:00 p.m., Domingos 9:00 a.m. - 6:00 p.m."""
    },
    
    "precios_compra_venta": {
        "keywords": ["precio", "precios", "mejor precio", "mercado", "comprar", "vender", "cotización", "oferta"],
        "contenido": """**Si compras:** Kavak ofrece excelentes precios en una plataforma con miles de vehículos usados de todo tipo y estilo. Si el auto que buscas no aparece en el catálogo, te ayudan a encontrarlo.

**Si vendes:** Kavak puede ofrecer tres opciones:
• Ofrecer depósito
• Pagar dentro de los 30 días  
• Pagar ahora

Depende de la demanda de tu automóvil en el mercado. Si optas por realizar un depósito y tu vehículo cumple con los estándares de calidad, el día de la inspección puedes firmar un contrato, pedirles que recojan el vehículo y al momento de la venta realizan el pago acordado."""
    },
    
    "certificacion_calidad": {
        "keywords": ["certificado", "certificación", "100%", "calidad", "inspección", "evaluación", "garantía"],
        "contenido": """**Autos 100% certificados:** Todos los autos que salen al mercado a través de Kavak pasan por una evaluación integral antes de ser comprados.

El proceso de inspección integral incluye:
• Evaluación del diseño exterior
• Inspección del interior
• Revisión del motor
• Inspectores especializados

Esto asegura la calidad del sello Kavak en todos los vehículos de la cartera de la marca."""
    },
    
    "auto_como_enganche": {
        "keywords": ["vehículo como pago", "medio de pago", "enganche", "anticipo", "auto actual", "intercambio"],
        "contenido": """**Tu vehículo como medio de pago:** Kavak te ofrece la posibilidad de usar tu vehículo actual como anticipo para comprar otro auto.

**Proceso:**
1. Dale a tu vehículo una cotización
2. Programa una inspección
3. Si cumple con los estándares de calidad, fijan el precio final
4. Este monto se establece como anticipo en la solicitud de financiamiento del vehículo de tu elección
5. Pagas el resto del auto nuevo a meses"""
    },
    
    "plan_pagos_financiamiento": {
        "keywords": ["plan de pago", "pagos", "meses", "financiamiento", "crédito", "mensual", "como funciona"],
        "contenido": """**Plan de pago a meses:** Con el plan de Kavak, puedes comprar tu auto pagando un monto mensual que se adapte a tus necesidades.

**¿Cómo funciona?**
1. **Solicita tu plan** - Conoce en menos de 2 minutos las opciones disponibles
2. **Completa los datos** - Ingresa y valida tu información
3. **Realiza el primer pago** - Asegura tu compra y domicilia los pagos mensuales
4. **Agenda la entrega** - Firma el contrato y recibe las llaves

**Documentación necesaria:**
• Identificación oficial (INE o pasaporte)
• Comprobante de domicilio reciente
• Comprobantes de ingresos (nómina, estados de cuenta, declaraciones)

Cuentan con diferentes modelos de plan de pagos. Su personal calificado busca lo mejor para ti evaluando tu historial crediticio."""
    },
    
    "proceso_digital": {
        "keywords": ["digital", "papeleo", "trámites", "online", "videollamada", "casa", "sin salir", "kavak.com"],
        "contenido": """**Todo el papeleo se realiza de forma digital:** Sin necesidad de visitar un centro ni salir de casa.

**Proceso simple:**
1. Ingresa al catálogo en línea en kavak.com
2. Selecciona el auto usado que más te guste
3. Haz clic en "Me interesa"
4. Selecciona la opción de cita por videollamada

**Videollamada:** Nuestro equipo de expertos se conecta contigo para mostrarte todos los detalles del auto (interior y exterior) y responder todas tus preguntas.

**Opciones después de la videollamada:**
• Proceder al pago directamente
• Agendar una reserva a domicilio donde llevan el auto hasta tu hogar sin compromiso"""
    },
    
    "periodo_prueba": {
        "keywords": ["periodo de prueba", "devolución", "devolver", "7 días", "300 km", "garantía", "3 meses"],
        "contenido": """**Periodo de prueba y devolución:** Cuando compras un auto seminuevo tienes:

• **7 días o 300 km** de periodo de prueba
• Si el auto no te convence, puedes devolverlo
• Kavak te ayuda a encontrar el auto de tus sueños
• **Garantía de 3 meses** incluida
• Posibilidad de **extender la garantía por un año más**"""
    },
    
    "app_postventa": {
        "keywords": ["app", "aplicación", "postventa", "mantenimiento", "servicios", "kavak total", "descargar"],
        "contenido": """**App Kavak - Servicios postventa:** Una aplicación donde cada cliente puede acceder a toda la información detallada de su vehículo.

**Funciones de la App:**
• Aplicar garantía
• Ampliar tu garantía a Kavak Total
• Agendar servicios de mantenimiento
• Consultar y solicitar trámites de tu auto
• Cotizar tu auto y obtener una oferta
• Consultar el catálogo completo

**Servicios de mantenimiento disponibles:**
• Básico, media vida y larga vida
• Con Kavak Total: dos servicios básicos incluidos a partir del sexto mes

**Tecnología:** Kavak apuesta por la tecnología como herramienta fundamental para mejorar procesos y brindar mejores experiencias, manteniendo siempre la vanguardia y evolución."""
    },
    
    "ventajas_generales": {
        "keywords": ["beneficios", "ventajas", "por qué kavak", "transparente", "seguro", "confianza"],
        "contenido": """**Beneficios principales de Kavak:**

• **Experiencia única y conveniente** en compra/venta de autos
• **Proceso transparente y seguro** 
• **Amplia red de sedes** en diferentes ciudades de México
• **Extensa variedad** de vehículos seminuevos de alta calidad
• **Plataforma en línea** completa para explorar inventario
• **Información detallada** de cada auto disponible
• **Opciones de financiamiento** a medida
• **Prueba de manejo** y garantía incluida
• **Atención personalizada** por equipo de expertos
• **Tecnología de vanguardia** en todos los procesos

Kavak es el aliado en quien confiar para que gestione los trámites necesarios y ofrezca beneficios reales, haciendo que comprar o vender un auto deje de ser un dolor de cabeza."""
    }
}


def buscar_informacion(query: str) -> str:
    """
    Busca información relevante basada en keywords en la consulta
    
    Args:
        query: Consulta del usuario
        
    Returns:
        Información relevante encontrada
    """
    query_lower = query.lower()
    
    # Buscar matches por keywords
    matches_encontrados = []
    
    for seccion_key, seccion_data in PROPUESTA_VALOR.items():
        score = 0
        for keyword in seccion_data["keywords"]:
            if keyword in query_lower:
                score += 1
        
        if score > 0:
            matches_encontrados.append((score, seccion_key, seccion_data))
    
    # Ordenar por score (más matches = más relevante)
    matches_encontrados.sort(key=lambda x: x[0], reverse=True)
    
    if matches_encontrados:
        # Retornar la sección con más matches
        return matches_encontrados[0][2]["contenido"]
    
    # Si no encuentra keywords específicas, retornar info general
    return PROPUESTA_VALOR["empresa_general"]["contenido"]


def obtener_todas_las_secciones() -> str:
    """
    Retorna todas las secciones disponibles para consultas generales
    
    Returns:
        Lista de todas las secciones disponibles
    """
    secciones = []
    for key, data in PROPUESTA_VALOR.items():
        secciones.append(f"• {key.replace('_', ' ').title()}")
    
    return "Información disponible sobre Kavak:\n" + "\n".join(secciones)