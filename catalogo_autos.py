"""
Módulo para manejar el catálogo de autos
Leer CSV, filtrar y recomendar autos según preferencias del usuario
"""

import pandas as pd
import re
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CatalogoAutos:
    """
    Clase para manejar el catálogo de autos desde CSV
    """
    
    def __init__(self, archivo_csv: str = "sample_caso_ai_engineer.csv"):
        """
        Inicializar catálogo
        
        Args:
            archivo_csv: Ruta del archivo CSV con el catálogo
        """
        self.archivo_csv = archivo_csv
        self.df = None
        self.cargar_catalogo()
    
    def cargar_catalogo(self) -> None:
        """Cargar el catálogo desde CSV"""
        try:
            self.df = pd.read_csv(self.archivo_csv)
            logger.info(f"Catálogo cargado: {len(self.df)} autos disponibles")
        except Exception as e:
            logger.error(f"Error cargando catálogo: {e}")
            # Crear DataFrame vacío como fallback
            self.df = pd.DataFrame()
    
    def buscar_autos(self, preferencias: str) -> List[Dict[str, Any]]:
        """
        Buscar autos basado en preferencias del usuario
        
        Args:
            preferencias: Texto con preferencias del usuario
            
        Returns:
            Lista de autos recomendados
        """
        if self.df.empty:
            return []
        
        # Extraer filtros del texto de preferencias
        filtros = self._extraer_filtros(preferencias)
        
        # Aplicar filtros
        df_filtrado = self._aplicar_filtros(filtros)
        
        # Ordenar por relevancia
        df_ordenado = self._ordenar_resultados(df_filtrado, filtros)
        
        # Tomar top 5 resultados
        top_autos = df_ordenado.head(5)
        
        # Convertir a lista de diccionarios
        return top_autos.to_dict('records')
        
    def _extraer_filtros(self, preferencias: str) -> Dict[str, Any]:
        """
        Extraer filtros del texto de preferencias
        
        Args:
            preferencias: Texto con preferencias
            
        Returns:
            Diccionario con filtros extraídos
        """
        filtros = {}
        texto_lower = preferencias.lower()
        
        # PASO 1: Extraer año PRIMERO para evitar confusión con precios
        años_encontrados = []
        patron_año = r'(20\d{2}|19\d{2})'
        años = re.findall(patron_año, texto_lower)
        if años:
            año = int(años[0])
            filtros['año_min'] = año
            años_encontrados.append(años[0])
        
        # Buscar palabras clave para año
        if 'nuevo' in texto_lower or 'reciente' in texto_lower:
            filtros['año_min'] = 2020
        elif 'viejo' in texto_lower or 'antiguo' in texto_lower:
            filtros['año_max'] = 2015
        
        # PASO 2: Extraer presupuesto SOLO con contexto específico
        palabras_precio = ['pesos', 'mx', 'mxn', 'presupuesto', 'precio', 'hasta', 'máximo', 'mil', 'k']
        
        # Solo buscar precio si hay palabras contextuales
        if any(palabra in texto_lower for palabra in palabras_precio):
            # Patrón más específico que excluye años ya encontrados
            patron_precio = r'(\d{1,3}(?:,?\d{3})*(?:\.\d{2})?)\s*(?:pesos|mx|mxn|mil|k|máximo|hasta)?'
            precios = re.findall(patron_precio, texto_lower.replace(',', ''))
            
            for precio_str in precios:
                # Saltar si es un año ya identificado
                if precio_str in años_encontrados:
                    continue
                    
                try:
                    precio_max = float(precio_str.replace(',', ''))
                    # Si es menor a 1000, probablemente son miles
                    if precio_max < 1000:
                        precio_max *= 1000
                    # Validar que sea un precio razonable para autos
                    if 50000 <= precio_max <= 2000000:
                        filtros['precio_max'] = precio_max
                        break
                except:
                    continue
        
        # PASO 3: Extraer marca y modelo específico - MEJORADO SIMPLE
        marcas_conocidas = self.df['make'].str.lower().unique() if not self.df.empty else []
        
        # Primero buscar marca explícita
        marca_encontrada = None
        for marca in marcas_conocidas:
            if marca in texto_lower:
                filtros['marca'] = marca.title()
                marca_encontrada = marca
                break
        
        # Buscar modelo específico
        if marca_encontrada:
            # Si hay marca, buscar modelos de esa marca
            modelos_marca = self.df[self.df['make'].str.lower() == marca_encontrada]['model'].str.lower().unique()
            for modelo in modelos_marca:
                if modelo in texto_lower:
                    filtros['modelo'] = modelo.title()
                    break
                elif modelo.replace(' ', '') in texto_lower.replace(' ', ''):
                    filtros['modelo'] = modelo.title()
                    break
        else:
            # NUEVO: Si no hay marca, buscar modelo en TODA la base
            todos_los_modelos = self.df['model'].str.lower().unique() if not self.df.empty else []
            for modelo in todos_los_modelos:
                if modelo in texto_lower:
                    # Encontrar la marca de este modelo (tomar la primera)
                    marca_del_modelo = self.df[self.df['model'].str.lower() == modelo]['make'].iloc[0]
                    filtros['modelo'] = modelo.title()
                    filtros['marca'] = marca_del_modelo
                    break
                elif modelo.replace(' ', '') in texto_lower.replace(' ', ''):
                    marca_del_modelo = self.df[self.df['model'].str.lower() == modelo]['make'].iloc[0]
                    filtros['modelo'] = modelo.title()
                    filtros['marca'] = marca_del_modelo
                    break
        
        # PASO 4: Extraer kilometraje
        if 'pocos kilómetros' in texto_lower or 'bajo kilometraje' in texto_lower:
            filtros['km_max'] = 50000
        elif 'muchos kilómetros' in texto_lower or 'alto kilometraje' in texto_lower:
            filtros['km_min'] = 100000
        
        # PASO 5: Características específicas
        if 'bluetooth' in texto_lower:
            filtros['bluetooth'] = 'Sí'
        if 'carplay' in texto_lower or 'car play' in texto_lower:
            filtros['car_play'] = 'Sí'
        
        return filtros
                
    def _aplicar_filtros(self, filtros: Dict[str, Any]) -> pd.DataFrame:
        """
        Aplicar filtros al DataFrame
        
        Args:
            filtros: Diccionario con filtros
            
        Returns:
            DataFrame filtrado
        """
        df_filtrado = self.df.copy()
        
        # Filtro por precio máximo
        if 'precio_max' in filtros:
            df_filtrado = df_filtrado[df_filtrado['price'] <= filtros['precio_max']]
        
        # Filtro por marca
        if 'marca' in filtros:
            df_filtrado = df_filtrado[df_filtrado['make'].str.lower() == filtros['marca'].lower()]
        
        # Filtro por modelo específico (NUEVO)
        if 'modelo' in filtros:
            df_filtrado = df_filtrado[df_filtrado['model'].str.lower() == filtros['modelo'].lower()]
        
        # Filtro por año mínimo
        if 'año_min' in filtros:
            df_filtrado = df_filtrado[df_filtrado['year'] >= filtros['año_min']]
        
        # Filtro por año máximo
        if 'año_max' in filtros:
            df_filtrado = df_filtrado[df_filtrado['year'] <= filtros['año_max']]
        
        # Filtro por kilometraje máximo
        if 'km_max' in filtros:
            df_filtrado = df_filtrado[df_filtrado['km'] <= filtros['km_max']]
        
        # Filtro por kilometraje mínimo
        if 'km_min' in filtros:
            df_filtrado = df_filtrado[df_filtrado['km'] >= filtros['km_min']]
        
        # Filtro por bluetooth
        if 'bluetooth' in filtros:
            df_filtrado = df_filtrado[df_filtrado['bluetooth'] == filtros['bluetooth']]
        
        # Filtro por car play
        if 'car_play' in filtros:
            df_filtrado = df_filtrado[df_filtrado['car_play'] == filtros['car_play']]
        
        return df_filtrado

    def _ordenar_resultados(self, df: pd.DataFrame, filtros: Dict[str, Any]) -> pd.DataFrame:
        """
        Ordenar resultados por relevancia
        
        Args:
            df: DataFrame a ordenar
            filtros: Filtros aplicados
            
        Returns:
            DataFrame ordenado
        """
        if df.empty:
            return df
        
        # Orden por defecto: precio ascendente, año descendente, km ascendente
        return df.sort_values(['price', 'year', 'km'], ascending=[True, False, True])
    
    def obtener_auto_por_stock_id(self, stock_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtener auto específico por stock_id
        
        Args:
            stock_id: ID del auto
            
        Returns:
            Diccionario con datos del auto o None
        """
        if self.df.empty:
            return None
        
        auto = self.df[self.df['stock_id'] == stock_id]
        if not auto.empty:
            return auto.iloc[0].to_dict()
        return None
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del catálogo
        
        Returns:
            Diccionario con estadísticas
        """
        if self.df.empty:
            return {}
        
        return {
            'total_autos': len(self.df),
            'marcas_disponibles': sorted(self.df['make'].unique().tolist()),
            'rango_precios': {
                'min': self.df['price'].min(),
                'max': self.df['price'].max(),
                'promedio': self.df['price'].mean()
            },
            'rango_años': {
                'min': self.df['year'].min(),
                'max': self.df['year'].max()
            },
            'autos_con_bluetooth': len(self.df[self.df['bluetooth'] == 'Sí']),
            'autos_con_carplay': len(self.df[self.df['car_play'] == 'Sí'])
        }


def formatear_auto_para_respuesta(auto: Dict[str, Any]) -> str:
    """
    Formatear información de un auto para respuesta del chatbot
    
    Args:
        auto: Diccionario con datos del auto
        
    Returns:
        String formateado para mostrar al usuario
    """
    precio_formateado = f"${auto.get('price', 0):,.0f} MXN"
    km_formateado = f"{auto.get('km', 0):,} km"
    
    info_auto = f"""**{auto.get('make', 'N/A')} {auto.get('model', 'N/A')} {auto.get('year', 'N/A')}**
                Precio: {precio_formateado}
                Kilometraje: {km_formateado}
                Bluetooth: {'Sí' if auto.get('bluetooth') == 'Sí' else 'No'}
                CarPlay: {'Sí' if auto.get('car_play') == 'Sí' else 'No'}
                Versión: {auto.get('version', 'N/A')}
                ID: {auto.get('stock_id', 'N/A')}"""
    
    return info_auto


def formatear_lista_autos(autos: List[Dict[str, Any]]) -> str:
    """
    Formatear lista de autos para respuesta del chatbot
    
    Args:
        autos: Lista de autos
        
    Returns:
        String formateado con la lista de autos
    """
    if not autos:
        return "No encontré autos que coincidan con tus preferencias. ¿Podrías ajustar los criterios de búsqueda?"
    
    respuesta = f"Encontré {len(autos)} auto(s) que podrían interesarte:\n\n"
    
    for i, auto in enumerate(autos, 1):
        respuesta += f"{i}. {formatear_auto_para_respuesta(auto)}\n\n"
    
    respuesta += "¿Te interesa alguno en particular? Puedo darte más detalles o ayudarte con el financiamiento."
    
    return respuesta