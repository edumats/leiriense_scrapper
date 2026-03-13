"""Convert a Leiriense Excel export into the "tiny" schema.

The script reads an input ``.xlsx`` file whose header row contains the
fields produced by the Leiriense system (see problem statement for the
exact list).  It then builds a new workbook with the much larger set of
headers expected by the target import layout, filling each column
according to the mapping rules provided by the user.

Usage::

    python convert_tiny.py in.xlsx out.xlsx

If the output path is omitted the converter will write ``converted.xlsx``
in the current working directory.

Dependencies: pandas, openpyxl

    pip install pandas openpyxl
"""

import argparse
import ast
import json
from pathlib import Path
from typing import Any

import pandas as pd


def _parse_imagens(val) -> list[str]:
    """Return a list of URLs parsed from the imagens column.

    The original cell contains a Python list literal such as
    ``['url1', 'url2']``.  ``ast.literal_eval`` handles the conversion
    safely; if parsing fails we return an empty list.
    """

    # if pandas has already interpreted the cell as a sequence, use it
    if isinstance(val, (list, tuple)):
        return [str(x) for x in val if x is not None]

    if not isinstance(val, str) or not val.strip():
        return []
    # val is a string, try to parse Python literal
    try:
        parsed = ast.literal_eval(val)
        if isinstance(parsed, (list, tuple)):
            # ensure each element is string
            return [str(x) for x in parsed if x is not None]
    except Exception:
        pass
    return []


def _parse_marca(categorias_val: str) -> str:
    """Extract the brand name from the categorias JSON-like string.

    According to the spec, the value is a list of dicts and the second
    element contains the brand in its ``'nome'`` key.
    """

    # handle cases where pandas already parsed the value
    if isinstance(categorias_val, (list, tuple)):
        if len(categorias_val) >= 2 and isinstance(categorias_val[1], dict):
            return str(categorias_val[1].get("nome", ""))
        return ""

    if isinstance(categorias_val, dict):
        # maybe the dict itself has a nome key
        return str(categorias_val.get("nome", ""))

    if not isinstance(categorias_val, str):
        return ""

    s = categorias_val.strip()
    if not s:
        return ""

    # try both Python literal and JSON loads (some exports are JSON)
    for loader in (ast.literal_eval, json.loads):
        try:
            parsed = loader(s)
        except Exception:
            continue
        if isinstance(parsed, (list, tuple)) and len(parsed) >= 2 and isinstance(parsed[1], dict):
            return str(parsed[1].get("nome", ""))
        if isinstance(parsed, dict):
            return str(parsed.get("nome", ""))

    return ""


def convert_file(input_path: Path, output_path: Path) -> None:
    # read input workbook (first sheet assumed)
    df = pd.read_excel(input_path)

    # clean column names: strip whitespace and stray commas
    df.columns = [col.strip().strip(",") for col in df.columns]

    # output headers in specified order
    out_headers = [
        "ID", "Código (SKU)", "Descrição", "Unidade", "Classificação fiscal",
        "Origem", "Preço", "Valor IPI fixo", "Observações", "Situação",
        "Estoque", "Preço de custo", "Cód do Fornecedor", "Fornecedor",
        "Localização", "Estoque máximo", "Estoque mínimo", "Peso líquido (Kg)",
        "Peso bruto (Kg)", "GTIN/EAN", "GTIN/EAN tributável",
        "Descrição complementar", "CEST", "Código de Enquadramento IPI",
        "Formato embalagem", "Largura embalagem", "Altura embalagem",
        "Comprimento embalagem", "Diâmetro embalagem", "Tipo do produto",
        "URL imagem 1", "URL imagem 2", "URL imagem 3", "URL imagem 4",
        "URL imagem 5", "URL imagem 6", "Categoria", "Código do pai",
        "Variações", "Marca", "Garantia", "Sob encomenda",
        "Preço promocional", "URL imagem externa 1", "URL imagem externa 2",
        "URL imagem externa 3", "URL imagem externa 4", "URL imagem externa 5",
        "URL imagem externa 6", "Link do vídeo", "Título SEO",
        "Descrição SEO", "Palavras chave SEO", "Slug", "Dias para preparação",
        "Controlar lotes", "Unidade por caixa", "URL imagem externa 7",
        "URL imagem externa 8", "URL imagem externa 9", "URL imagem externa 10",
        "Markup", "Permitir inclusão nas vendas", "EX TIPI",
    ]

    out_rows: list[dict] = []

    for _, row in df.iterrows():
        # build output row dictionary
        out: dict[str, Any] = {h: "" for h in out_headers}

        out["ID"] = ""
        codigo = str(row.get("codigo", ""))
        out["Código (SKU)"] = "LEIRI" + codigo
        out["Descrição"] = row.get("nome", "")
        out["Unidade"] = row.get("unidade", "")
        out["Classificação fiscal"] = ""
        out["Origem"] = (
            "2 - Estrangeira - Adquirida no mercado interno, exceto a indicada no código 7"
        )
        out["Preço"] = ""
        out["Valor IPI fixo"] = 0
        out["Observações"] = ""
        out["Situação"] = "Ativo"
        out["Estoque"] = row.get("saldo_estoque", "")
        out["Preço de custo"] = row.get("preco_com_tributos", "")
        out["Cód do Fornecedor"] = row.get("codigo", "")
        out["Fornecedor"] = "CICLO LEIRIENSE PECAS E ACESSORIOS PARA BICICLETAS LTDA"
        out["Localização"] = ""
        out["Estoque máximo"] = 0
        out["Estoque mínimo"] = 1
        out["Peso líquido (Kg)"] = ""
        out["Peso bruto (Kg)"] = ""
        out["GTIN/EAN"] = ""
        out["GTIN/EAN tributável"] = ""
        out["Descrição complementar"] = row.get("informacoes_adicionais", "")
        out["CEST"] = ""
        out["Código de Enquadramento IPI"] = ""
        out["Formato embalagem"] = "Pacote / Caixa"
        out["Largura embalagem"] = ""
        out["Altura embalagem"] = ""
        out["Comprimento embalagem"] = ""
        out["Diâmetro embalagem"] = ""
        out["Tipo do produto"] = "S"

        # handle imagens list
        imgs = _parse_imagens(row.get("imagens", ""))
        for idx, url in enumerate(imgs[:6], start=1):
            out[f"URL imagem {idx}"] = url

        out["Categoria"] = ""
        out["Código do pai"] = ""
        out["Variações"] = ""
        out["Marca"] = _parse_marca(row.get("categorias", ""))
        out["Garantia"] = "3 meses"
        out["Sob encomenda"] = "Não"
        out["Preço promocional"] = ""
        # external URL slots remain blank by default
        out["Link do vídeo"] = ""
        out["Título SEO"] = row.get("nome", "")
        out["Descrição SEO"] = row.get("informacoes_adicionais", "")
        out["Palavras chave SEO"] = ""
        out["Slug"] = ""
        out["Dias para preparação"] = 0
        out["Controlar lotes"] = "Não"
        out["Unidade por caixa"] = ""
        out["Markup"] = 0
        out["Permitir inclusão nas vendas"] = "Sim"
        out["EX TIPI"] = ""

        out_rows.append(out)

    # create DataFrame and write to Excel
    out_df = pd.DataFrame(out_rows, columns=out_headers)
    out_df.to_excel(output_path, index=False)


def main():
    parser = argparse.ArgumentParser(description="Convert Excel file to tiny format")
    parser.add_argument("input", help="input xlsx file")
    parser.add_argument("output", nargs="?", default="converted.xlsx",
                        help="output xlsx file")
    args = parser.parse_args()

    convert_file(Path(args.input), Path(args.output))


if __name__ == "__main__":
    main()
