/**
 * Sesión de la persona (DO-2026-10-22-WEB F3). El token de acceso vive en memoria; con
 * Cognito, el de renovación se guarda en `sessionStorage` (se borra al cerrar la pestaña).
 * Los permisos efectivos los decide siempre el backend: aquí solo se ocultan acciones.
 */
import { createContext, type ReactNode, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

import { api, conectarSesion, exigir } from "@/api/cliente";
import type { Rol, Yo } from "@/api/tipos";

import { ingresarConCognito, renovarConCognito } from "./cognito";
import { CONFIGURACION } from "./configuracion";
import { cargaDelToken } from "./jwt";

const CLAVE_REFRESCO = "atlas.refresco";
// Solo en desarrollo local (WEB F3): el token pegado sobrevive a una recarga de la pestaña.
const CLAVE_TOKEN_LOCAL = "atlas.token_local";

interface Tokens {
  acceso: string;
  refresco: string | null;
  expiraEn: number;
}

interface ValorSesion {
  cargando: boolean;
  yo: Yo | null;
  tiene: (rol: Rol) => boolean;
  ingresar: (usuario: string, clave: string) => Promise<void>;
  ingresarConToken: (token: string) => Promise<void>;
  salir: () => void;
}

const ContextoSesion = createContext<ValorSesion | null>(null);

function leer(clave: string): string | null {
  try {
    return sessionStorage.getItem(clave);
  } catch {
    return null;
  }
}

function guardar(clave: string, valor: string | null): void {
  try {
    if (valor) sessionStorage.setItem(clave, valor);
    else sessionStorage.removeItem(clave);
  } catch {
    // Sin almacenamiento disponible: la sesión dura lo que la página.
  }
}

const guardarRefresco = (valor: string | null) => guardar(CLAVE_REFRESCO, valor);

export function ProveedorSesion({ children }: { children: ReactNode }) {
  const tokens = useRef<Tokens | null>(null);
  const [yo, setYo] = useState<Yo | null>(null);
  const [cargando, setCargando] = useState(true);

  const salir = useCallback(() => {
    tokens.current = null;
    guardarRefresco(null);
    guardar(CLAVE_TOKEN_LOCAL, null);
    setYo(null);
  }, []);

  const tokenVigente = useCallback(async (): Promise<string | null> => {
    const actual = tokens.current;
    if (!actual) return null;
    const restante = actual.expiraEn - Date.now() / 1000;
    if (restante > 60 || !actual.refresco) return restante > 0 ? actual.acceso : null;
    const renovado = await renovarConCognito(actual.refresco);
    tokens.current = { ...renovado, refresco: renovado.refresco ?? actual.refresco };
    return renovado.acceso;
  }, []);

  useEffect(() => {
    conectarSesion(tokenVigente, salir);
  }, [tokenVigente, salir]);

  const abrir = useCallback(async (nuevos: Tokens) => {
    tokens.current = nuevos;
    try {
      setYo(await exigir(api.GET("/usuarios/yo")));
      guardarRefresco(nuevos.refresco);
      if (CONFIGURACION.autenticacion === "local") guardar(CLAVE_TOKEN_LOCAL, nuevos.acceso);
    } catch (error) {
      tokens.current = null;
      throw error;
    }
  }, []);

  useEffect(() => {
    if (CONFIGURACION.autenticacion === "local") {
      const token = leer(CLAVE_TOKEN_LOCAL);
      const exp = token ? cargaDelToken(token)?.exp : undefined;
      if (token && exp && exp > Date.now() / 1000) {
        abrir({ acceso: token, refresco: null, expiraEn: exp })
          .catch(() => guardar(CLAVE_TOKEN_LOCAL, null))
          .finally(() => setCargando(false));
      } else setCargando(false);
      return;
    }
    const refresco = leer(CLAVE_REFRESCO);
    if (!refresco) {
      setCargando(false);
      return;
    }
    renovarConCognito(refresco)
      .then((renovado) => abrir({ ...renovado, refresco: renovado.refresco ?? refresco }))
      .catch(() => guardarRefresco(null))
      .finally(() => setCargando(false));
  }, [abrir]);

  const valor = useMemo<ValorSesion>(
    () => ({
      cargando,
      yo,
      tiene: (rol) => !!yo?.roles.includes(rol),
      ingresar: async (usuario, clave) => abrir(await ingresarConCognito(usuario, clave)),
      ingresarConToken: async (token) => {
        const carga = cargaDelToken(token.trim());
        if (!carga?.exp) throw new Error("El texto pegado no es un token de acceso válido.");
        await abrir({ acceso: token.trim(), refresco: null, expiraEn: carga.exp });
      },
      salir,
    }),
    [abrir, cargando, salir, yo],
  );

  return <ContextoSesion.Provider value={valor}>{children}</ContextoSesion.Provider>;
}

export function useSesion(): ValorSesion {
  const valor = useContext(ContextoSesion);
  if (!valor) throw new Error("useSesion fuera de ProveedorSesion");
  return valor;
}
