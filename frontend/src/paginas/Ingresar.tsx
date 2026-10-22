import { LogIn } from "lucide-react";
import { type FormEvent, useState } from "react";
import { Navigate, useLocation } from "react-router";

import { Aviso } from "@/componentes/ui/aviso";
import { Boton } from "@/componentes/ui/boton";
import { AreaTexto, Ayuda, Entrada, Etiqueta } from "@/componentes/ui/campos";
import { mensajeDeError } from "@/componentes/ui/estados";
import { CONFIGURACION } from "@/lib/configuracion";
import { useSesion } from "@/lib/sesion";

export function Ingresar() {
  const { yo, ingresar, ingresarConToken } = useSesion();
  const ubicacion = useLocation();
  const [usuario, setUsuario] = useState("");
  const [clave, setClave] = useState("");
  const [token, setToken] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  if (yo) return <Navigate to={(ubicacion.state as { desde?: string } | null)?.desde ?? "/"} replace />;
  const local = CONFIGURACION.autenticacion === "local";

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    setError(null);
    setEnviando(true);
    try {
      if (local) await ingresarConToken(token);
      else await ingresar(usuario, clave);
    } catch (e) {
      setError(mensajeDeError(e));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="grid min-h-screen place-items-center px-4">
      <form onSubmit={enviar} className="w-full max-w-sm space-y-5 rounded-lg border border-borde bg-superficie p-8">
        <div>
          <span className="grid size-10 place-items-center rounded-md bg-primario font-bold text-white">A</span>
          <h1 className="mt-4 text-xl">Ingresar a ATLAS</h1>
          <p className="mt-1 text-sm text-tenue">Gestión de documentos y contratos con trazabilidad.</p>
        </div>
        {local ? (
          <div className="space-y-1.5">
            <Etiqueta htmlFor="token">Token de acceso (desarrollo local)</Etiqueta>
            <AreaTexto id="token" value={token} onChange={(e) => setToken(e.target.value)} required className="font-mono text-xs" />
            <Ayuda>Emitilo con python -m atlas.herramientas.token_local --sub &lt;sub&gt;.</Ayuda>
          </div>
        ) : (
          <>
            <div className="space-y-1.5">
              <Etiqueta htmlFor="usuario">Usuario</Etiqueta>
              <Entrada id="usuario" autoComplete="username" value={usuario} onChange={(e) => setUsuario(e.target.value)} required />
            </div>
            <div className="space-y-1.5">
              <Etiqueta htmlFor="clave">Contraseña</Etiqueta>
              <Entrada id="clave" type="password" autoComplete="current-password" value={clave} onChange={(e) => setClave(e.target.value)} required />
            </div>
          </>
        )}
        {error ? <Aviso tono="peligro" titulo={error} /> : null}
        <Boton type="submit" className="w-full" disabled={enviando}>
          <LogIn /> {enviando ? "Ingresando…" : "Ingresar"}
        </Boton>
      </form>
    </div>
  );
}
