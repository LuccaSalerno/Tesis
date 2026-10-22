/**
 * Recorridos críticos (DO-2026-10-22-WEB): la evidencia de una decisión observada (punto D) y
 * la validación de un dato con su fuente (punto A), sobre la semilla local PD-07.
 * Requiere ATLAS_E2E_TOKEN_RESPONSABLE (token local del responsable de la semilla).
 */
import { expect, type Page, test } from "@playwright/test";

const token = process.env.ATLAS_E2E_TOKEN_RESPONSABLE ?? "";

async function ingresar(page: Page) {
  await page.goto("/ingresar");
  await page.getByLabel("Token de acceso (desarrollo local)").fill(token);
  await page.getByRole("button", { name: "Ingresar" }).click();
  await expect(page.getByRole("heading", { name: /^Hola/ })).toBeVisible();
}

test.skip(!token, "Falta ATLAS_E2E_TOKEN_RESPONSABLE");

test("D: desde el historial se reconstruye la decisión observada", async ({ page }) => {
  await ingresar(page);
  await page.getByRole("link", { name: "Servicio de mantenimiento de laboratorio", exact: true }).first().click();
  await page.getByRole("link", { name: "Historial" }).click();
  await page.getByRole("link", { name: "Evidencia de la decisión" }).first().click();
  await expect(page.getByRole("heading", { name: "Evidencia de la decisión" })).toBeVisible();
  await expect(page.getByText(/fuera de la vigencia del contrato/).first()).toBeVisible();
  await page.getByRole("button", { name: /^R3 ·/ }).click();
  await expect(page.getByRole("button", { name: /^R3 ·/ })).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "Ver en el documento" }).first().click();
  await expect(page.getByRole("dialog")).toContainText("C-v1_Contrato_Mantenimiento_ATLAS.pdf");
});

test("A: el contrato en vivo muestra sugerencias rotuladas y su fuente", async ({ page }) => {
  await ingresar(page);
  await page.getByRole("link", { name: /\(en vivo\)/ }).first().click();
  await page.getByRole("link", { name: "Documentos y datos" }).click();
  await page.getByRole("link", { name: /Validar datos/ }).first().click();
  await expect(page.getByRole("heading", { name: "Tipo documental" })).toBeVisible();
  await expect(page.getByText("Sugerido").first()).toBeVisible();
  await expect(page.getByText("Simulación local").first()).toBeVisible();
  await expect(page.getByText(/Página 1 de 10/)).toBeVisible();
});
