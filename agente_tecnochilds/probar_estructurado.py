import time
from typing import Literal
from pydantic import BaseModel
from core.graph import modelo

class Decision(BaseModel):
    ruta: Literal["conceptual", "herramientas"]
    motivo: str

print("Modelo:", modelo.model)
t = time.time()
r = modelo.with_structured_output(Decision).invoke("Quiero carreras para un perfil científico")
print(r, f"({time.time() - t:.1f} s)")