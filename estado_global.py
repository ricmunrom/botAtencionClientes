from typing import Dict, Any, Optional, List
from datetime import datetime

class EstadoGlobal:
    """
    Clase para manejar el estado global compartido entre todas las tools del agente.
    Almacena información del contexto de la conversación como auto seleccionado, 
    preferencias del cliente, cálculos de financiamiento, etc.
    """
    
    def __init__(self):
        """Inicializar el estado global con valores por defecto"""
        self._estado = {
            # Información del cliente
            'cliente_nombre': None,
            'cliente_telefono': None,
            'cliente_preferencias': {},
            
            # Auto seleccionado/recomendado
            'auto_seleccionado': None,
            'auto_precio': None,
            'auto_marca': None,
            'auto_modelo': None,
            'auto_año': None,
            
            # Financiamiento
            'enganche': None,
            'plazo_años': None,
            'tasa_interes': 0.10,  # 10% fijo
            'pago_mensual': None,
            'monto_financiar': None,
            
            # Contexto de conversación
            'ultima_consulta': None,
            'ultimo_mensaje': None,
            'ultima_respuesta': None,
            'timestamp': datetime.now(),
            'historial_acciones': []
        }
    
    def obtener(self, clave: str) -> Any:
        """
        Obtener valor del estado global
        
        Args:
            clave: Clave del valor a obtener
            
        Returns:
            Valor asociado a la clave o None si no existe
        """
        return self._estado.get(clave)
    
    def actualizar(self, clave: str, valor: Any) -> None:
        """
        Actualizar un valor en el estado global
        
        Args:
            clave: Clave a actualizar
            valor: Nuevo valor
        """
        self._estado[clave] = valor
        self._estado['timestamp'] = datetime.now()
        
        # Registrar acción en historial
        accion = {
            'timestamp': datetime.now(),
            'accion': f'actualizar_{clave}',
            'valor': str(valor)[:100]  # Limitar longitud para logging
        }
        self._estado['historial_acciones'].append(accion)
    
    def actualizar_multiple(self, datos: Dict[str, Any]) -> None:
        """
        Actualizar múltiples valores del estado global
        
        Args:
            datos: Diccionario con claves y valores a actualizar
        """
        for clave, valor in datos.items():
            self._estado[clave] = valor
        
        self._estado['timestamp'] = datetime.now()
        
        # Registrar acción en historial
        accion = {
            'timestamp': datetime.now(),
            'accion': 'actualizar_multiple',
            'claves': list(datos.keys())
        }
        self._estado['historial_acciones'].append(accion)
    
    def obtener_info_auto(self) -> Dict[str, Any]:
        """
        Obtener toda la información del auto seleccionado
        
        Returns:
            Diccionario con información del auto o diccionario vacío
        """
        return {
            'auto_seleccionado': self._estado.get('auto_seleccionado'),
            'auto_precio': self._estado.get('auto_precio'),
            'auto_marca': self._estado.get('auto_marca'),
            'auto_modelo': self._estado.get('auto_modelo'),
            'auto_año': self._estado.get('auto_año')
        }
    
    def obtener_info_financiamiento(self) -> Dict[str, Any]:
        """
        Obtener toda la información de financiamiento
        
        Returns:
            Diccionario con información de financiamiento
        """
        return {
            'enganche': self._estado.get('enganche'),
            'plazo_años': self._estado.get('plazo_años'),
            'tasa_interes': self._estado.get('tasa_interes'),
            'pago_mensual': self._estado.get('pago_mensual'),
            'monto_financiar': self._estado.get('monto_financiar'),
            'auto_precio': self._estado.get('auto_precio')
        }
    
    def limpiar_auto(self) -> None:
        """Limpiar información del auto seleccionado"""
        claves_auto = ['auto_seleccionado', 'auto_precio', 'auto_marca', 'auto_modelo', 'auto_año']
        for clave in claves_auto:
            self._estado[clave] = None
        self._estado['timestamp'] = datetime.now()
    
    def limpiar_financiamiento(self) -> None:
        """Limpiar información de financiamiento manteniendo tasa fija"""
        claves_financiamiento = ['enganche', 'plazo_años', 'pago_mensual', 'monto_financiar']
        for clave in claves_financiamiento:
            self._estado[clave] = None
        self._estado['tasa_interes'] = 0.10  # Mantener tasa fija del 10%
        self._estado['timestamp'] = datetime.now()
    
    def reiniciar(self) -> None:
        """Reiniciar todo el estado global manteniendo info básica del cliente"""
        telefono = self._estado.get('cliente_telefono')
        nombre = self._estado.get('cliente_nombre')
        
        self.__init__()  # Reiniciar estado
        
        # Restaurar info básica del cliente si existía
        if telefono:
            self._estado['cliente_telefono'] = telefono
        if nombre:
            self._estado['cliente_nombre'] = nombre
    
    def obtener_resumen(self) -> Dict[str, Any]:
        """
        Obtener resumen del estado actual
        
        Returns:
            Diccionario con resumen del estado
        """
        return {
            'cliente': self._estado.get('cliente_nombre'),
            'telefono': self._estado.get('cliente_telefono'),
            'auto_info': self.obtener_info_auto(),
            'financiamiento_info': self.obtener_info_financiamiento(),
            'ultima_consulta': self._estado.get('ultima_consulta'),
            'ultimo_mensaje': self._estado.get('ultimo_mensaje'),
            'timestamp': self._estado.get('timestamp'),
            'total_acciones': len(self._estado.get('historial_acciones', []))
        }
    
    def __str__(self) -> str:
        """Representación string del estado para debugging"""
        resumen = self.obtener_resumen()
        return f"EstadoGlobal({resumen})"


class GestorEstados:
    """
    Gestor centralizado de estados por usuario.
    Mantiene un estado separado para cada número de teléfono.
    """
    
    def __init__(self):
        """Inicializar gestor de estados"""
        self._estados_usuarios: Dict[str, EstadoGlobal] = {}
    
    def obtener_estado(self, telefono: str) -> EstadoGlobal:
        """
        Obtener el estado para un usuario específico
        
        Args:
            telefono: Número de teléfono del usuario
            
        Returns:
            Estado global del usuario
        """
        if telefono not in self._estados_usuarios:
            # Crear nuevo estado para usuario
            self._estados_usuarios[telefono] = EstadoGlobal()
            self._estados_usuarios[telefono].actualizar('cliente_telefono', telefono)
            print(f"Nuevo estado creado para usuario: {telefono}")
        
        return self._estados_usuarios[telefono]
    
    def eliminar_estado(self, telefono: str) -> bool:
        """
        Eliminar estado de un usuario
        
        Args:
            telefono: Número de teléfono del usuario
            
        Returns:
            True si se eliminó, False si no existía
        """
        if telefono in self._estados_usuarios:
            del self._estados_usuarios[telefono]
            print(f"Estado eliminado para usuario: {telefono}")
            return True
        return False
    
    def reiniciar_estado(self, telefono: str) -> None:
        """
        Reiniciar estado de un usuario específico
        
        Args:
            telefono: Número de teléfono del usuario
        """
        if telefono in self._estados_usuarios:
            self._estados_usuarios[telefono].reiniciar()
        else:
            # Crear nuevo estado si no existe
            self._estados_usuarios[telefono] = EstadoGlobal()
            self._estados_usuarios[telefono].actualizar('cliente_telefono', telefono)
    
    def obtener_usuarios_activos(self) -> List[str]:
        """
        Obtener lista de usuarios con estados activos
        
        Returns:
            Lista de números de teléfono con estados
        """
        return list(self._estados_usuarios.keys())
    
    def obtener_resumen_general(self) -> Dict[str, Any]:
        """
        Obtener resumen de todos los estados
        
        Returns:
            Diccionario con información de todos los usuarios
        """
        return {
            'total_usuarios': len(self._estados_usuarios),
            'usuarios_activos': self.obtener_usuarios_activos(),
            'estados_por_usuario': {
                telefono: estado.obtener_resumen() 
                for telefono, estado in self._estados_usuarios.items()
            }
        }
    
    def limpiar_estados_antiguos(self, horas: int = 24) -> int:
        """
        Limpiar estados de usuarios inactivos por más de X horas
        
        Args:
            horas: Horas de inactividad para considerar estado antiguo
            
        Returns:
            Número de estados eliminados
        """
        ahora = datetime.now()
        estados_eliminar = []
        
        for telefono, estado in self._estados_usuarios.items():
            ultimo_timestamp = estado.obtener('timestamp')
            if ultimo_timestamp:
                diferencia = ahora - ultimo_timestamp
                if diferencia.total_seconds() > (horas * 3600):
                    estados_eliminar.append(telefono)
        
        for telefono in estados_eliminar:
            self.eliminar_estado(telefono)
        
        return len(estados_eliminar)