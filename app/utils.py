"""
Utilidades auxiliares para el sistema de tickets.
"""

def formatear_monto(monto: float) -> str:
    """
    Formatea un número decimal como moneda en Soles (S/).
    """
    return f"S/ {monto:.2f}"
