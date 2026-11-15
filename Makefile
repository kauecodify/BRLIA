SHELL := /bin/bash
PROFILE ?= all

.PHONY: help up down seed reconcile test migrate attach detach bench-pool scan

help:
	@echo "up            sobe a plataforma (PROFILE=br|intl|all|colocated)"
	@echo "seed          aplica o genesis de R$ 100.000.000,00"
	@echo "reconcile     reconcilia genesis, pool e ledger"
	@echo "test          executa a suíte de testes"
	@echo "migrate       aplica migracoes do PostgreSQL"
	@echo "attach        acopla o agente ao host sem restart"
	@echo "detach        drena a janela e desacopla"
	@echo "bench-pool    executa tests/pool/bench_pool.py (operador)"

up:
	./scripts/start.sh --profile $(PROFILE)

down:
	./scripts/stop.sh

seed:
	./scripts/apply-seed.sh

reconcile:
	./scripts/reconcile.sh

test:
	python3 -m unittest discover -s tests -p "test_*.py" 2>/dev/null || python3 -m pytest tests -q

migrate:
	./scripts/migrate.sh

attach:
	./scripts/attach.sh

detach:
	./scripts/detach.sh

bench-pool:
	./scripts/bench-pool.sh

scan:
	./scripts/scan_hotpath.sh
