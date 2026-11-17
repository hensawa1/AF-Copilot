"""Experimento real de fine-tuning local (resultados preliminares).

Não substitui o Gemini 3.5 Flash Lite em produção: é um experimento acadêmico
de calibração, executado em CPU, com modelo causal pequeno. Mede loss antes e
depois do treino, latência de inferência e custo (R$ 0 em CPU local).
"""

from __future__ import annotations

import json
import platform
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "datasets" / "finetune.jsonl"
OUT = ROOT / "docs" / "evidencias" / "finetune_treino.txt"
AMBIENTE = ROOT / "docs" / "evidencias" / "finetune_ambiente.txt"
MODEL_DIR = ROOT / "runtime" / "finetune-model"
MODELO = "pierreguillou/gpt2-small-portuguese"
FALLBACK = "distilgpt2"
EPOCHS = 3
MAX_LEN = 192


def linhas() -> list[str]:
    return []


def registrar(reg: list[str], msg: str = "") -> None:
    reg.append(msg)
    print(msg, flush=True)


def carregar():
    registros = [json.loads(l) for l in DATA.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert all({"instruction", "input", "output"} <= set(r) for r in registros)
    return registros[:16], registros[16:]


def exemplo(r: dict) -> str:
    pergunta = f"{r['instruction']} {r['input']}".strip()
    return f"Pergunta: {pergunta}\nResposta: {r['output']}{tokenizer.eos_token}"


def batch_de(texto: str):
    ids = tokenizer.encode(texto, add_special_tokens=False)[:MAX_LEN]
    if not ids:
        ids = [tokenizer.eos_token_id or 0]
    return {
        "input_ids": torch.tensor([ids], dtype=torch.long),
        "attention_mask": torch.tensor([[1] * len(ids)], dtype=torch.long),
        "labels": torch.tensor([ids], dtype=torch.long),
    }


@torch.no_grad()
def loss_validacao(model, val) -> float:
    model.eval()
    total = 0.0
    for r in val:
        b = batch_de(exemplo(r))
        total += float(model(**b).loss)
    model.train()
    return total / max(1, len(val))


def main() -> None:
    global tokenizer
    torch.set_num_threads(4)
    reg = linhas()
    treino, val = carregar()

    registrar(reg, "=== FINE-TUNING LOCAL — EXPERIMENTO PRELIMINAR ===")
    registrar(reg, f"dataset: {len(treino) + len(val)} pares | treino={len(treino)} | validacao={len(val)}")
    registrar(reg, "amostra: Pergunta: metformina 850 mg E11 diabetes / Resposta: ...")
    registrar(reg, f"python={platform.python_version()} | torch={torch.__version__} | transformers={__import__('transformers').__version__}")
    registrar(reg, f"cpu={platform.processor() or 'x86_64'} | nucleos={torch.get_num_threads()} | cuda={torch.cuda.is_available()}")
    registrar(reg, f"modelo_base={MODELO} | fallback={FALLBACK} | epochs={EPOCHS} | max_len={MAX_LEN}")
    AMBIENTE.write_text("\n".join(reg[:8]) + "\n", encoding="utf-8")

    usado = MODELO
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODELO)
        model = AutoModelForCausalLM.from_pretrained(MODELO)
    except Exception as exc:  # noqa: BLE001
        registrar(reg, f"modelo portugues indisponivel ({type(exc).__name__}); usando {FALLBACK}")
        usado = FALLBACK
        tokenizer = AutoTokenizer.from_pretrained(FALLBACK)
        model = AutoModelForCausalLM.from_pretrained(FALLBACK)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    registrar(reg, f"modelo_carregado={usado} | parametros={sum(p.numel() for p in model.parameters()):,}")

    base = loss_validacao(model, val)
    registrar(reg, f"loss_validacao_base={base:.4f} | perplexidade_base={__import__('math').exp(min(base, 20)):.2f}")

    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5)
    inicio = time.perf_counter()
    for ep in range(1, EPOCHS + 1):
        epoch_loss = 0.0
        for r in treino:
            b = batch_de(exemplo(r))
            optimizer.zero_grad()
            loss = model(**b).loss
            loss.backward()
            optimizer.step()
            epoch_loss += float(loss)
        medio = epoch_loss / len(treino)
        registrar(reg, f"epoch {ep}/{EPOCHS} | loss_treino={medio:.4f}")
    tempo = time.perf_counter() - inicio

    final = loss_validacao(model, val)
    registrar(reg, f"loss_validacao_final={final:.4f} | perplexidade_final={__import__('math').exp(min(final, 20)):.2f}")
    delta = (base - final) / base * 100 if base else 0.0
    registrar(reg, f"variacao_loss={delta:+.1f}% | tempo_treino={tempo:.1f}s | custo_cpu=R$ 0,00")

    t0 = time.perf_counter()
    loss_validacao(model, val[:1])
    lat = (time.perf_counter() - t0) * 1000
    registrar(reg, f"latencia_inferencia_local={lat:.0f} ms (1 exemplo, CPU, forward)")
    registrar(reg, "conclusao: treino executado com sucesso; modelo salvo em runtime/finetune-model (ignorado pelo git).")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(MODEL_DIR)
    tokenizer.save_pretrained(MODEL_DIR)
    OUT.write_text("\n".join(reg) + "\n", encoding="utf-8")
    print("SALVO", OUT, flush=True)


if __name__ == "__main__":
    main()
