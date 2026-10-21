"""Tests locales del verificador de inventario; no requieren AWS ni pytest."""
import csv
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'herramientas'))
from validar_inventario_e90 import validar_inventario


class InventarioE90Tests(unittest.TestCase):
    def preparar(self, base: Path):
        (base / 'corpus').mkdir()
        records = []
        for tipo in ('contrato', 'presupuesto', 'orden_compra', 'factura', 'comprobante'):
            for grupo, cantidad in (('medicion', 10), ('ajuste', 2)):
                for i in range(cantidad):
                    ext = '.docx' if i == 1 else '.pdf'
                    name = f'corpus/{tipo}_{grupo}_{i}{ext}'
                    data = f'{name}:fixture_sintetico'.encode()
                    (base / name).write_bytes(data)
                    formato = 'docx' if ext == '.docx' else ('pdf_escaneado' if i == 2 else 'pdf_digital')
                    records.append({
                        'doc_id': f'{tipo}-{grupo}-{i}', 'grupo': grupo, 'tipo': tipo,
                        'formato': formato,
                        'plantilla_id': f'{tipo}-exclusiva' if grupo == 'medicion' else f'{tipo}-ajuste',
                        'ruta': name, 'sha256': hashlib.sha256(data).hexdigest(),
                        'prompt_injection': 'si' if grupo == 'medicion' and tipo == 'contrato' and i < 3 else 'no',
                        'observaciones': '',
                    })
        file = base / 'inventario.csv'
        with file.open('w', newline='', encoding='utf8') as f:
            writer = csv.DictWriter(f, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
        return file, records

    def test_completo_valido(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            archivo, _ = self.preparar(base)
            self.assertEqual(validar_inventario(base, archivo), [])

    def test_falla_un_adversarial(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            archivo, registros = self.preparar(base)
            next(d for d in registros if d['prompt_injection'] == 'si')['prompt_injection'] = 'no'
            with archivo.open('w', newline='', encoding='utf8') as f:
                writer=csv.DictWriter(f, fieldnames=list(registros[0]))
                writer.writeheader();writer.writerows(registros)
            self.assertTrue(any('exactamente 3 adversariales' in v for v in validar_inventario(base, archivo)))

    def test_ruta_traversal_rechazada(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            archivo, registros = self.preparar(base)
            registros[0]['ruta'] = '../secreto.pdf'
            with archivo.open('w', newline='', encoding='utf8') as f:
                writer=csv.DictWriter(f, fieldnames=list(registros[0]))
                writer.writeheader();writer.writerows(registros)
            self.assertTrue(any('ruta no permitida' in v for v in validar_inventario(base, archivo)))

if __name__ == '__main__':
    unittest.main()
