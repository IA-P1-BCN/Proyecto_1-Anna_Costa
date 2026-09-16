"""
Taxímetro Digital — TaxiTech Solutions
Fase 1 — MVP Funcional (US-01 a US-04)

CLI que permite a un taxista iniciar una carrera, alternar entre estado
"parado" y "en movimiento", y finalizar la carrera para obtener el importe
total a cobrar. El importe se acumula de forma continua en función del
tiempo real transcurrido en cada estado.

Tarifas vigentes (Zona EMT Madrid, junio 2025):
  - Parado o velocidad < 20 km/h: 0.02 €/segundo
  - En movimiento:                0.05 €/segundo
"""

import time

TARIFA_PARADO = 0.02    # €/segundo
TARIFA_MOVIMIENTO = 0.05  # €/segundo

ESTADO_PARADO = "parado"
ESTADO_MOVIMIENTO = "movimiento"

COMANDOS_VALIDOS = {"m", "p", "f"}


class Taximetro:
    """Gestiona el estado y el cálculo de tarifa de una única carrera."""

    def __init__(self):
        self.estado = None
        self.importe_acumulado = 0.0
        self.instante_ultimo_cambio = None
        self.en_curso = False

    def _tarifa_actual(self):
        return TARIFA_PARADO if self.estado == ESTADO_PARADO else TARIFA_MOVIMIENTO

    def _acumular_hasta_ahora(self):
        ahora = time.time()
        segundos_transcurridos = ahora - self.instante_ultimo_cambio
        self.importe_acumulado += segundos_transcurridos * self._tarifa_actual()
        self.instante_ultimo_cambio = ahora

    def iniciar_carrera(self):
        self.estado = ESTADO_PARADO
        self.importe_acumulado = 0.0
        self.instante_ultimo_cambio = time.time()
        self.en_curso = True
        print("\n🚕 Carrera iniciada. Estado inicial: PARADO.")

    def cambiar_estado(self, nuevo_estado):
        if nuevo_estado == self.estado:
            print(f"\nYa estás en estado '{nuevo_estado.upper()}'.")
            return
        self._acumular_hasta_ahora()
        self.estado = nuevo_estado
        print(f"\n🔄 Estado cambiado a: {nuevo_estado.upper()}")

    def finalizar_carrera(self):
        self._acumular_hasta_ahora()
        self.en_curso = False
        total = self.importe_acumulado
        print(f"\n🏁 Carrera finalizada. Importe total a cobrar: {total:.2f} €")
        return total


def mostrar_instrucciones():
    print("=" * 52)
    print("🚕  TAXÍMETRO DIGITAL — TaxiTech Solutions")
    print("=" * 52)
    print("Tarifas vigentes:")
    print(f"  · Parado o < 20 km/h : {TARIFA_PARADO:.2f} €/segundo")
    print(f"  · En movimiento      : {TARIFA_MOVIMIENTO:.2f} €/segundo")
    print()
    print("Comandos disponibles durante una carrera:")
    print("  m -> cambiar a EN MOVIMIENTO")
    print("  p -> cambiar a PARADO")
    print("  f -> FINALIZAR la carrera y ver el importe total")
    print("=" * 52)


def pedir_comando():
    comando = input("\nComando (m/p/f): ").strip().lower()
    while comando not in COMANDOS_VALIDOS:
        print("⚠️  Comando no válido. Usa 'm', 'p' o 'f'.")
        comando = input("Comando (m/p/f): ").strip().lower()
    return comando


def ejecutar_carrera(taximetro):
    taximetro.iniciar_carrera()
    while taximetro.en_curso:
        comando = pedir_comando()
        if comando == "m":
            taximetro.cambiar_estado(ESTADO_MOVIMIENTO)
        elif comando == "p":
            taximetro.cambiar_estado(ESTADO_PARADO)
        elif comando == "f":
            taximetro.finalizar_carrera()


def main():
    mostrar_instrucciones()
    taximetro = Taximetro()

    while True:
        respuesta = input("\n¿Iniciar nueva carrera? (s/n): ").strip().lower()
        if respuesta != "s":
            print("\n👋 Fin del turno. ¡Buen día!")
            break
        ejecutar_carrera(taximetro)


if __name__ == "__main__":
    main()
