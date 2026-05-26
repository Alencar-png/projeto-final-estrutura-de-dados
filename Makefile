PYTHON ?= python3
PYTHONPATH := $(CURDIR)
export PYTHONPATH

.PHONY: help install gen-basico gen-avancado gen-estresse gen-all run-basico run-avancado run-estresse verify-basico verify-avancado clean stress relatorio relatorio-pdf

help:
	@echo "Alvos disponíveis:"
	@echo "  make install        Instala dependências de geração de dados (Faker)"
	@echo "  make gen-basico     Gera data/input_basico.json + gabarito"
	@echo "  make gen-avancado   Gera data/input_avancado.json + gabarito"
	@echo "  make gen-estresse   Gera data/input_estresse.json (50k palavras / 10k docs)"
	@echo "  make gen-all        Gera os 3 cenários completos"
	@echo "  make run-basico     Executa o motor sobre input_basico.json"
	@echo "  make run-avancado   Executa o motor sobre input_avancado.json"
	@echo "  make run-estresse   Executa o motor sobre input_estresse.json"
	@echo "  make verify-basico  Compara saída real x esperada (básico)"
	@echo "  make verify-avancado Compara saída real x esperada (avançado)"
	@echo "  make stress         Mede tempo/memória no cenário de estresse"
	@echo "  make relatorio      Gera o relatório acadêmico em DOCX"
	@echo "  make relatorio-pdf  Gera relatório DOCX e converte para PDF (requer LibreOffice)"
	@echo "  make clean          Remove caches e saídas geradas"

install:
	$(PYTHON) -m pip install -r requirements.txt

gen-basico:
	$(PYTHON) -m src.generators.generate_data --cenario basico --out data/

gen-avancado:
	$(PYTHON) -m src.generators.generate_data --cenario avancado --out data/

gen-estresse:
	$(PYTHON) -m src.generators.generate_data --cenario estresse --out data/

gen-all: gen-basico gen-avancado gen-estresse

run-basico:
	$(PYTHON) -m src.main --input data/input_basico.json --output data/output_real_basico.json

run-avancado:
	$(PYTHON) -m src.main --input data/input_avancado.json --output data/output_real_avancado.json

run-estresse:
	$(PYTHON) -m src.main --input data/input_estresse.json --output data/output_real_estresse.json

verify-basico: run-basico
	$(PYTHON) -m src.tools.diff_outputs data/output_esperado_basico.json data/output_real_basico.json

verify-avancado: run-avancado
	$(PYTHON) -m src.tools.diff_outputs data/output_esperado_avancado.json data/output_real_avancado.json

stress:
	$(PYTHON) -m src.tools.stress_bench --input data/input_estresse.json

relatorio:
	$(PYTHON) docs/relatorio/gerar_relatorio.py

relatorio-pdf: relatorio
	soffice --headless --convert-to pdf docs/relatorio/Relatorio_Motor_RAG.docx --outdir docs/relatorio/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -f data/output_real_*.json output.json
