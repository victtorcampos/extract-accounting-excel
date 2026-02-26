# Escritório Contábil Sorriso - Extrator de Lançamentos

Sistema automatizado para conversão de extratos Excel em arquivos de importação contábil (TXT Registro 6100).

## 🚀 Funcionalidades
- **Upload de Excel (Página 1):** Suporta arquivos até 10MB via Base64.
- **Motor de Parsing:** Processamento assíncrono utilizando `python-calamine` (alta performance).
- **Gestão de Pendências (Página 2):** Interface para mapear contas desconhecidas encontradas no Excel.
- **Histórico (Página 3):** Consulta de protocolos por CNPJ e download de arquivos processados.

## 🛠️ Stack Técnica
- **Backend:** FastAPI, SQLModel (SQLAlchemy), SQLite (Modo WAL).
- **Frontend:** HTML5, TailwindCSS (CDN), JavaScript Vanilla.
- **Parsing:** Python-Calamine.

## ⚙️ Como Executar
1. **Ambiente Virtual:**
   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install .

```

2. **Inicializar Banco:**
```powershell
$env:PYTHONPATH = (Get-Item .).FullName
python app/seed.py

```


3. **Rodar Servidor:**
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8111 --reload

```

Acesse: `http://localhost:8111`