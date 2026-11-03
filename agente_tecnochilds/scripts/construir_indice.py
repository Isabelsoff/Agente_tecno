from core.rag import construir_indice


if __name__ == "__main__":
    cantidad = construir_indice()
    print(f"Índice RAG construido con {cantidad} programas.")
