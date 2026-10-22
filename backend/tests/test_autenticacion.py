"""Verificación de tokens de acceso sin AWS (DT-AUT-01, RF-01, RNF-01)."""

import base64
import hashlib
import hmac
import json
import time
from pathlib import Path

import jwt
import pytest

from atlas.autenticacion.claves_locales import CLIENTE_LOCAL, EMISOR_LOCAL, ClavesLocales
from atlas.autenticacion.verificador import ErrorAutenticacion, VerificadorJwt
from atlas.configuracion import ErrorConfiguracion
from atlas.herramientas import token_local
from tests.conftest import CLAVES_PRUEBA, configuracion_sin_base

EMISOR_COGNITO = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_AbC123"


@pytest.fixture
def verificador() -> VerificadorJwt:
    return VerificadorJwt(CLAVES_PRUEBA.jwks(), emisor=EMISOR_LOCAL, cliente=CLIENTE_LOCAL)


def test_rf_01_token_de_acceso_valido(verificador: VerificadorJwt) -> None:
    identidad = verificador.verificar(CLAVES_PRUEBA.emitir("sub-valido"))
    assert identidad.identificador_externo == "sub-valido"


def _sin_firma() -> str:
    ahora = int(time.time())
    return jwt.encode(
        {
            "sub": "x",
            "iss": EMISOR_LOCAL,
            "client_id": CLIENTE_LOCAL,
            "token_use": "access",
            "iat": ahora,
            "exp": ahora + 60,
        },
        None,
        algorithm="none",
        headers={"kid": CLAVES_PRUEBA.kid},
    )


def _sin_kid() -> str:
    return jwt.encode({"sub": "x"}, CLAVES_PRUEBA.privada, algorithm="RS256")


def _sin_client_id() -> str:
    ahora = int(time.time())
    return jwt.encode(
        {"sub": "x", "iss": EMISOR_LOCAL, "token_use": "access", "iat": ahora, "exp": ahora + 60},
        CLAVES_PRUEBA.privada,
        algorithm="RS256",
        headers={"kid": CLAVES_PRUEBA.kid},
    )


def _firmado_con_otra_clave() -> str:
    otra = ClavesLocales.generar()
    return ClavesLocales(otra.privada, CLAVES_PRUEBA.kid).emitir("x")


@pytest.mark.parametrize(
    ("token", "codigo"),
    [
        pytest.param(
            lambda: CLAVES_PRUEBA.emitir("x", vigencia_s=-10), "token_vencido", id="vencido"
        ),
        pytest.param(
            lambda: CLAVES_PRUEBA.emitir("x", emisor=EMISOR_COGNITO), "emisor_invalido", id="emisor"
        ),
        pytest.param(
            lambda: CLAVES_PRUEBA.emitir("x", cliente="otro-cliente"),
            "cliente_invalido",
            id="cliente",
        ),
        pytest.param(
            lambda: CLAVES_PRUEBA.emitir("x", token_use="id"),
            "tipo_de_token_invalido",
            id="token_id",
        ),
        pytest.param(lambda: CLAVES_PRUEBA.emitir(""), "token_invalido", id="sub_vacio"),
        pytest.param(_firmado_con_otra_clave, "firma_invalida", id="otra_clave"),
        pytest.param(_sin_firma, "algoritmo_no_admitido", id="alg_none"),
        pytest.param(_sin_kid, "clave_desconocida", id="sin_kid"),
        pytest.param(
            lambda: ClavesLocales.generar().emitir("x"), "clave_desconocida", id="kid_ajeno"
        ),
        pytest.param(_sin_client_id, "token_invalido", id="sin_client_id"),
        pytest.param(lambda: "no-es-un-jwt", "token_malformado", id="malformado"),
    ],
)
def test_rnf_01_tokens_rechazados(verificador: VerificadorJwt, token: object, codigo: str) -> None:
    with pytest.raises(ErrorAutenticacion) as rechazo:
        verificador.verificar(token())  # type: ignore[operator]
    assert rechazo.value.codigo == codigo


def test_rnf_01_confusion_de_algoritmo_hs256_rechazada(verificador: VerificadorJwt) -> None:
    """Un token HS256 firmado con la clave pública como secreto no debe aceptarse."""

    def b64(datos: bytes) -> str:
        return base64.urlsafe_b64encode(datos).rstrip(b"=").decode()

    encabezado = b64(json.dumps({"alg": "HS256", "kid": CLAVES_PRUEBA.kid}).encode())
    carga = b64(json.dumps({"sub": "x"}).encode())
    secreto = json.dumps(CLAVES_PRUEBA.jwks()["keys"][0]).encode()
    firma = b64(hmac.new(secreto, f"{encabezado}.{carga}".encode(), hashlib.sha256).digest())
    with pytest.raises(ErrorAutenticacion, match="algoritmo_no_admitido"):
        verificador.verificar(f"{encabezado}.{carga}.{firma}")


def test_dt_aut_01_jwks_sin_claves_rsa_rechazado() -> None:
    with pytest.raises(ValueError, match="RSA"):
        VerificadorJwt({"keys": []}, emisor=EMISOR_LOCAL, cliente=CLIENTE_LOCAL)


@pytest.mark.parametrize(
    ("campos", "mensaje"),
    [
        ({"jwt_emisor": None}, "ATLAS_JWT_EMISOR"),
        ({"entorno": "demo"}, "User Pool de Cognito"),
        ({"jwt_jwks": None}, "exactamente uno"),
        ({"jwt_jwks_archivo": Path("jwks.json")}, "exactamente uno"),
    ],
)
def test_rc_p10_configuracion_de_tokens_invalida(campos: dict[str, object], mensaje: str) -> None:
    with pytest.raises(ErrorConfiguracion, match=mensaje):
        configuracion_sin_base(**campos).cargar_jwks()


def test_rc_p10_demo_acepta_emisor_de_cognito() -> None:
    configuracion = configuracion_sin_base(entorno="demo", jwt_emisor=EMISOR_COGNITO)
    assert configuracion.cargar_jwks() == CLAVES_PRUEBA.jwks()


def test_dt_aut_01_token_local_genera_claves_y_emite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(token_local, "obtener_configuracion", configuracion_sin_base)
    directorio = tmp_path / "claves"
    assert token_local.main(["--sub", "sub-local", "--directorio", str(directorio)]) == 0
    token = capsys.readouterr().out.strip()
    configuracion = configuracion_sin_base(jwt_jwks=None, jwt_jwks_archivo=directorio / "jwks.json")
    verificador = VerificadorJwt(configuracion.cargar_jwks(), EMISOR_LOCAL, CLIENTE_LOCAL)
    assert verificador.verificar(token).identificador_externo == "sub-local"
    assert (directorio / "privada.pem").stat().st_mode & 0o077 == 0
    # Una segunda emisión reutiliza las mismas claves.
    assert token_local.main(["--sub", "otro", "--directorio", str(directorio)]) == 0
    assert verificador.verificar(capsys.readouterr().out.strip()).identificador_externo == "otro"


def test_dt_aut_01_token_local_rechazado_en_demo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        token_local,
        "obtener_configuracion",
        lambda: configuracion_sin_base(entorno="demo", jwt_emisor=EMISOR_COGNITO),
    )
    assert token_local.main(["--sub", "x", "--directorio", str(tmp_path)]) == 1
    assert not (tmp_path / "privada.pem").exists()
