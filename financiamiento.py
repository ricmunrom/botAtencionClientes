"""
Módulo para manejar cálculos y lógica de financiamiento
Separado de FinanzasTool para mantener consistencia arquitectónica
"""

import re
from typing import Dict, Any, Optional, List

# Constantes del sistema de financiamiento
TASA_INTERES_ANUAL = 0.10  # 10% fijo
PLAZOS_PERMITIDOS = [3, 4, 5, 6]  # años
PORCENTAJES_ENGANCHE_SUGERIDOS = [0.10, 0.20, 0.30]  # 10%, 20%, 30%

class CalculadoraFinanciamiento:
    """
    Clase para manejar todos los cálculos de financiamiento
    """
    
    @staticmethod
    def calcular_pago_mensual(monto_financiar: float, años: int) -> float:
        """
        Calcular pago mensual con fórmula de financiamiento
        
        Args:
            monto_financiar: Monto a financiar
            años: Años del plazo
            
        Returns:
            Pago mensual
        """
        if monto_financiar <= 0:
            return 0
        
        tasa_mensual = TASA_INTERES_ANUAL / 12
        num_pagos = años * 12
        
        # Fórmula de financiamiento: PMT = [P × r × (1 + r)^n] / [(1 + r)^n - 1]
        if tasa_mensual == 0:
            return monto_financiar / num_pagos
        
        factor = (1 + tasa_mensual) ** num_pagos
        pago_mensual = (monto_financiar * tasa_mensual * factor) / (factor - 1)
        
        return pago_mensual
    
    @staticmethod
    def calcular_totales(monto_financiar: float, años: int) -> Dict[str, float]:
        """
        Calcular totales del financiamiento
        
        Args:
            monto_financiar: Monto a financiar
            años: Años del plazo
            
        Returns:
            Diccionario con pago mensual, total a pagar, total intereses
        """
        pago_mensual = CalculadoraFinanciamiento.calcular_pago_mensual(monto_financiar, años)
        total_pagos = pago_mensual * años * 12
        total_intereses = total_pagos - monto_financiar
        
        return {
            'pago_mensual': pago_mensual,
            'total_pagos': total_pagos,
            'total_intereses': total_intereses,
            'num_mensualidades': años * 12
        }

def extraer_enganche(texto: str, precio_auto: float) -> Optional[float]:
    """
    Extraer enganche del texto del usuario - VERSIÓN MEJORADA
    """
    texto_lower = texto.lower()
    
    # PRIMERO: Buscar patrones específicos de enganche
    patrones_enganche = [
        r'enganche\s*de\s*(\d{1,3}(?:,?\d{3})*)',
        r'dando\s*un\s*enganche\s*de\s*(\d{1,3}(?:,?\d{3})*)',
        r'con\s*(\d{1,3}(?:,?\d{3})*)\s*de\s*enganche',
        r'(\d{1,3}(?:,?\d{3})*)\s*pesos.*enganche'
    ]
    
    for patron in patrones_enganche:
        matches = re.findall(patron, texto_lower.replace(',', ''))
        if matches:
            try:
                monto = float(matches[0].replace(',', ''))
                if monto <= precio_auto:
                    print(f"DEBUG: Enganche encontrado con patrón específico: {monto}")
                    return monto
            except:
                continue
    
    # FALLBACK: Tu lógica original solo si no encuentra nada específico
    patron_monto = r'(\d{1,3}(?:,?\d{3})*(?:\.\d{2})?)\s*(?:pesos|mx|mxn)'
    montos = re.findall(patron_monto, texto_lower.replace(',', ''))
    
    if montos:
        try:
            monto = float(montos[0].replace(',', ''))
            if monto < 1000:
                monto *= 1000
            if monto <= precio_auto:
                print(f"DEBUG: Enganche encontrado con patrón fallback: {monto}")
                return monto
        except:
            pass
    
    print("DEBUG: No se encontró enganche válido")
    return None
    
def extraer_plazo(texto: str) -> Optional[int]:
    """
    Extraer plazo específico del texto
    
    Args:
        texto: Texto con parámetros de financiamiento
        
    Returns:
        Plazo en años o None
    """
    texto_lower = texto.lower()
    
    # Buscar patrones como "3 años", "a 4 años", "financiar a 5 años"
    patrones_plazo = [
        r'(\d)\s*años?',
        r'a\s*(\d)\s*años?',
        r'financiar\s*a\s*(\d)\s*años?',
        r'plazo\s*de\s*(\d)\s*años?'
    ]
    
    for patron in patrones_plazo:
        matches = re.findall(patron, texto_lower)
        if matches:
            try:
                plazo = int(matches[0])
                # Validar que esté en el rango permitido
                if plazo in PLAZOS_PERMITIDOS:
                    return plazo
            except:
                pass
    
    return None

def generar_plan_especifico(auto_info: Dict, precio_auto: float, enganche: float, 
                          plazo_especifico: Optional[int] = None) -> str:
    """
    Generar plan de financiamiento específico
    
    Args:
        auto_info: Información del auto
        precio_auto: Precio del auto
        enganche: Monto del enganche
        plazo_especifico: Plazo específico en años (opcional)
        
    Returns:
        Texto formateado con el plan
    """
    monto_financiar = precio_auto - enganche
    auto_descripcion = f"{auto_info.get('marca', 'N/A')} {auto_info.get('modelo', 'N/A')} {auto_info.get('año', 'N/A')}"
    
    respuesta = f"""Plan de financiamiento para {auto_descripcion}

                Precio del auto: ${precio_auto:,.0f} MXN
                Enganche: ${enganche:,.0f} MXN ({enganche/precio_auto*100:.1f}%)
                Monto a financiar: ${monto_financiar:,.0f} MXN
                Tasa de interés: {TASA_INTERES_ANUAL*100:.0f}% anual

                """
    
    if plazo_especifico:
        # Plan específico para un plazo
        totales = CalculadoraFinanciamiento.calcular_totales(monto_financiar, plazo_especifico)
        
        respuesta += f"""Financiamiento a {plazo_especifico} años ({totales['num_mensualidades']} mensualidades)
                        Pago mensual: ${totales['pago_mensual']:,.0f} MXN
                        Total a pagar: ${totales['total_pagos']:,.0f} MXN
                        Total intereses: ${totales['total_intereses']:,.0f} MXN"""
        
    else:
        # Plan con múltiples opciones de plazo
        respuesta += "Opciones de pago mensual:\n"
        
        for años in PLAZOS_PERMITIDOS:
            totales = CalculadoraFinanciamiento.calcular_totales(monto_financiar, años)
            respuesta += f"""
                    {años} años ({totales['num_mensualidades']} mensualidades)
                       Pago mensual: ${totales['pago_mensual']:,.0f} MXN
                       Total a pagar: ${totales['total_pagos']:,.0f} MXN
                       Total intereses: ${totales['total_intereses']:,.0f} MXN
                    """
    
    respuesta += "\n\n¿Te interesa alguna de estas opciones? Puedo ayudarte con los siguientes pasos."
    
    return respuesta

def generar_opciones_multiples(auto_info: Dict, precio_auto: float) -> str:
    """
    Generar múltiples opciones de enganche y financiamiento
    
    Args:
        auto_info: Información del auto
        precio_auto: Precio del auto
        
    Returns:
        Texto formateado con múltiples opciones
    """
    auto_descripcion = f"{auto_info.get('marca', 'N/A')} {auto_info.get('modelo', 'N/A')} {auto_info.get('año', 'N/A')}"
    
    respuesta = f"""Opciones de financiamiento para {auto_descripcion}
                Precio: ${precio_auto:,.0f} MXN | Tasa: {TASA_INTERES_ANUAL*100:.0f}% anual

                """
    
    for porcentaje_enganche in PORCENTAJES_ENGANCHE_SUGERIDOS:
        enganche = precio_auto * porcentaje_enganche
        monto_financiar = precio_auto - enganche
        
        respuesta += f"""Con {porcentaje_enganche*100:.0f}% de enganche (${enganche:,.0f} MXN):""" 

        for años in PLAZOS_PERMITIDOS:
            pago_mensual = CalculadoraFinanciamiento.calcular_pago_mensual(monto_financiar, años)
            respuesta += f"   • {años} años: ${pago_mensual:,.0f}/mes\n"
        
        respuesta += "\n"
    
    respuesta += "¿Qué enganche y plazo te conviene más? Puedo darte más detalles de cualquier opción."
    
    return respuesta

def validar_auto_seleccionado(auto_precio: Optional[float]) -> bool:
    """
    Validar si hay un auto seleccionado con precio válido
    
    Args:
        auto_precio: Precio del auto seleccionado
        
    Returns:
        True si hay auto válido seleccionado
    """
    return auto_precio is not None and auto_precio > 0

def generar_mensaje_sin_auto() -> str:
    """
    Generar mensaje cuando no hay auto seleccionado
    
    Returns:
        Mensaje pidiendo seleccionar auto primero
    """
    return """Para calcular tu financiamiento necesito que primero selecciones un auto.

            Puedes buscar autos diciendo algo como:
            • "Quiero un Toyota con presupuesto de 300000"
            • "Muéstrame autos del 2020"
            • "Busco un auto con bluetooth"

            Una vez que selecciones un auto, podremos calcular las opciones de financiamiento perfectas para ti."""