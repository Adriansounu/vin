"""Generador de Números de Identificación Vehicular (NIV) - NOM-001-SSP-2008."""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings
from app.core.check_digit import calculate_check_digit
from app.core.niv_validator import validar_formato
from app.models import NIV, MapeoVDS, SerieContador
from app.utils.helpers import format_serie, has_prohibited_chars, year_to_code

logger = logging.getLogger(__name__)

# Posición del VDS -> categoría correspondiente en la tabla mapeo_vds.
VDS_CATEGORIES: dict[int, str] = {
    4: "tipo_remolque",
    6: "capacidad",
    7: "tipo_frenos",
    8: "version",
}

MAX_SERIE = 99999  # posiciones 13-17 (5 dígitos: 00001-99999)


class NIVGeneratorError(ValueError):
    """Error de negocio durante la generación de un NIV (entrada inválida o conflicto)."""


class NIVGenerator:
    """Genera NIVs completos y los persiste en base de datos de forma atómica."""

    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    def _lookup_mapeo(self, posicion: int, codigo: str) -> MapeoVDS:
        """Busca un código activo en la tabla de mapeo VDS para la posición dada."""
        categoria = VDS_CATEGORIES[posicion]
        stmt = select(MapeoVDS).where(
            MapeoVDS.posicion == posicion,
            MapeoVDS.codigo == codigo,
            MapeoVDS.activo.is_(True),
        )
        mapeo = self.db.execute(stmt).scalar_one_or_none()
        if mapeo is None:
            raise NIVGeneratorError(
                f"Código '{codigo}' inválido o inactivo para la categoría '{categoria}' (posición {posicion})."
            )
        return mapeo

    @staticmethod
    def _validar_ejes(num_ejes: int) -> None:
        if not 1 <= num_ejes <= 9:
            raise NIVGeneratorError("El número de ejes debe estar entre 1 y 9.")

    def _siguiente_serie(self, linea_produccion: int, anio_modelo: int) -> int:
        """Incrementa atómicamente el contador de serie por línea/año usando bloqueo de fila.

        El bloqueo (SELECT ... FOR UPDATE) evita colisiones cuando múltiples
        requests concurrentes generan NIVs para la misma línea y año.
        """
        stmt = (
            select(SerieContador)
            .where(
                SerieContador.linea_produccion == linea_produccion,
                SerieContador.anio_modelo == anio_modelo,
            )
            .with_for_update()
        )
        contador = self.db.execute(stmt).scalar_one_or_none()

        if contador is None:
            contador = SerieContador(
                linea_produccion=linea_produccion,
                anio_modelo=anio_modelo,
                ultimo_numero=0,
            )
            self.db.add(contador)
            self.db.flush()

        if contador.ultimo_numero >= MAX_SERIE:
            raise NIVGeneratorError(
                f"Se alcanzó el límite máximo de serie ({MAX_SERIE}) para la línea "
                f"{linea_produccion} en el año {anio_modelo}."
            )

        contador.ultimo_numero += 1
        self.db.flush()
        return contador.ultimo_numero

    def generate(
        self,
        tipo_remolque: str,
        num_ejes: int,
        capacidad: str,
        tipo_frenos: str,
        version: str,
        anio_modelo: int,
        linea_produccion: int,
        planta: str | None = None,
    ) -> NIV:
        """Genera y persiste un nuevo NIV. Retorna la instancia del modelo `NIV` creada."""
        self._validar_ejes(num_ejes)

        mapeo_tipo = self._lookup_mapeo(4, tipo_remolque.upper())
        mapeo_capacidad = self._lookup_mapeo(6, capacidad.upper())
        mapeo_frenos = self._lookup_mapeo(7, tipo_frenos.upper())
        mapeo_version = self._lookup_mapeo(8, version.upper())

        planta_codigo = (planta or self.settings.planta_default).upper()
        if len(planta_codigo) != 1 or not planta_codigo.isalpha():
            raise NIVGeneratorError("El código de planta debe ser una sola letra.")

        if not 1 <= linea_produccion <= 9:
            raise NIVGeneratorError("La línea de producción debe estar entre 1 y 9.")

        wmi = self.settings.wmi.upper()
        if len(wmi) != 3:
            raise NIVGeneratorError("El WMI configurado debe tener exactamente 3 caracteres.")

        vds = f"{mapeo_tipo.codigo}{num_ejes}{mapeo_capacidad.codigo}{mapeo_frenos.codigo}{mapeo_version.codigo}"

        codigo_anio = year_to_code(anio_modelo)
        numero_serie = self._siguiente_serie(linea_produccion, anio_modelo)
        vis = f"{codigo_anio}{planta_codigo}{linea_produccion}{format_serie(numero_serie)}"

        # Placeholder '0' en la posición 9 (peso 0, no afecta la suma ponderada).
        niv_sin_check = f"{wmi}{vds}0{vis}"
        prohibidos = has_prohibited_chars(niv_sin_check)
        if prohibidos:
            raise NIVGeneratorError(f"Caracteres prohibidos generados: {', '.join(prohibidos)}.")

        check_digit = calculate_check_digit(niv_sin_check)
        niv_completo = f"{wmi}{vds}{check_digit}{vis}"

        resultado_validacion = validar_formato(niv_completo)
        if not resultado_validacion.valido:
            raise NIVGeneratorError(
                f"El NIV generado no pasó la validación: {'; '.join(resultado_validacion.errores)}"
            )

        registro = NIV(
            niv=niv_completo,
            wmi=wmi,
            vds=vds,
            digito_verificador=check_digit,
            vis=vis,
            tipo_remolque=mapeo_tipo.descripcion,
            num_ejes=num_ejes,
            capacidad=mapeo_capacidad.descripcion,
            tipo_frenos=mapeo_frenos.descripcion,
            version=mapeo_version.descripcion,
            anio_modelo=anio_modelo,
            codigo_anio=codigo_anio,
            planta=planta_codigo,
            linea_produccion=linea_produccion,
            numero_serie=numero_serie,
        )

        try:
            self.db.add(registro)
            self.db.commit()
            self.db.refresh(registro)
        except IntegrityError as exc:
            self.db.rollback()
            logger.error("Conflicto de integridad al generar NIV %s: %s", niv_completo, exc)
            raise NIVGeneratorError(
                "El NIV generado ya existe en la base de datos (conflicto de concurrencia). Intente nuevamente."
            ) from exc

        logger.info("NIV generado exitosamente: %s", niv_completo)
        return registro
