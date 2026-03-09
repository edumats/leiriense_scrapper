"""Unit tests for convert_tiny.py"""

import unittest
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import sys

# add parent directory to path so we can import convert_tiny
sys.path.insert(0, str(Path(__file__).parent.parent))

from convert_tiny import _parse_imagens, _parse_marca, convert_file


class TestParseImagens(unittest.TestCase):
    """Tests for the _parse_imagens function."""

    def test_parse_valid_image_list(self):
        """Test parsing a valid Python list of image URLs."""
        img_str = "['https://example.com/img1.jpg', 'https://example.com/img2.jpg']"
        result = _parse_imagens(img_str)
        self.assertEqual(result, ['https://example.com/img1.jpg', 'https://example.com/img2.jpg'])
    
    def test_parse_3_images(self):
        """Test parsing a list with exactly 3 images."""
        img_str = "['https://arquivos.mercos.com/media/imagem_produto/271401/f5761d46-d4ac-11ee-87d5-4611ba22c79b.jpeg', 'https://arquivos.mercos.com/media/imagem_produto/271401/f3e77614-d4ac-11ee-8c91-3aadbe637912.jpeg', 'https://arquivos.mercos.com/media/imagem_produto/271401/f6d2269e-d4ac-11ee-adc4-6e0edaf22e78.jpeg']"
        result = _parse_imagens(img_str)
        self.assertEqual(result, [
            'https://arquivos.mercos.com/media/imagem_produto/271401/f5761d46-d4ac-11ee-87d5-4611ba22c79b.jpeg',
            'https://arquivos.mercos.com/media/imagem_produto/271401/f3e77614-d4ac-11ee-8c91-3aadbe637912.jpeg',
            'https://arquivos.mercos.com/media/imagem_produto/271401/f6d2269e-d4ac-11ee-adc4-6e0edaf22e78.jpeg',
        ])

    def test_parse_single_image(self):
        """Test parsing a list with a single image."""
        img_str = "['https://example.com/img1.jpg']"
        result = _parse_imagens(img_str)
        self.assertEqual(result, ['https://example.com/img1.jpg'])

    def test_parse_empty_list(self):
        """Test parsing an empty list."""
        img_str = "[]"
        result = _parse_imagens(img_str)
        self.assertEqual(result, [])

    def test_parse_empty_string(self):
        """Test parsing an empty string."""
        result = _parse_imagens("")
        self.assertEqual(result, [])

    def test_parse_none_value(self):
        """Test parsing None value."""
        result = _parse_imagens(None)
        self.assertEqual(result, [])

    def test_parse_invalid_syntax(self):
        """Test parsing invalid Python syntax returns empty list."""
        img_str = "not valid python"
        result = _parse_imagens(img_str)
        self.assertEqual(result, [])

    def test_parse_malformed_list(self):
        """Test parsing malformed list returns empty list."""
        img_str = "['url1', 'url2'"  # missing closing bracket
        result = _parse_imagens(img_str)
        self.assertEqual(result, [])

    def test_parse_tuple_format(self):
        """Test parsing tuple format (should also work)."""
        img_str = "('https://example.com/img1.jpg', 'https://example.com/img2.jpg')"
        result = _parse_imagens(img_str)
        self.assertEqual(result, ['https://example.com/img1.jpg', 'https://example.com/img2.jpg'])

    def test_parse_list_object(self):
        """If the cell already contains a Python list, return it directly."""
        lst = ['a', 'b', None]
        result = _parse_imagens(lst)
        self.assertEqual(result, ['a', 'b'])


class TestParseMarca(unittest.TestCase):
    """Tests for the _parse_marca function."""

    def test_parse_valid_marca(self):
        """Test parsing a valid categorias structure."""
        categorias_str = "[{'categoria_id': 1021274, 'nome': 'CADEADOS', 'categoria_pai_id': 1021203}, {'categoria_id': 1021203, 'nome': 'ABUS', 'categoria_pai_id': None}]"
        result = _parse_marca(categorias_str)
        self.assertEqual(result, "ABUS")

    def test_parse_marca_single_category(self):
        """Test parsing with only one category (should return empty)."""
        categorias_str = "[{'categoria_id': 1021274, 'nome': 'CADEADOS', 'categoria_pai_id': 1021203}]"
        result = _parse_marca(categorias_str)
        self.assertEqual(result, "")

    def test_parse_marca_empty_list(self):
        """Test parsing an empty list."""
        result = _parse_marca("[]")
        self.assertEqual(result, "")

    def test_parse_marca_none_value(self):
        """Test parsing None value."""
        result = _parse_marca(None)
        self.assertEqual(result, "")

    def test_parse_marca_invalid_syntax(self):
        """Test parsing invalid syntax returns empty string."""
        result = _parse_marca("not valid json")
        self.assertEqual(result, "")

    def test_parse_marca_missing_nome_key(self):
        """Test parsing second element without 'nome' key."""
        categorias_str = "[{'categoria_id': 1021274}, {'categoria_id': 1021203}]"
        result = _parse_marca(categorias_str)
        self.assertEqual(result, "")

    def test_parse_marca_castelli(self):
        """Test parsing a Castelli brand example."""
        categorias_str = "[{'categoria_id': 3180054, 'nome': 'ROUPAS', 'categoria_pai_id': None}, {'categoria_id': 3180054, 'nome': 'CASTELLI', 'categoria_pai_id': None}]"
        result = _parse_marca(categorias_str)
        self.assertEqual(result, "CASTELLI")

    def test_parse_marca_json_string(self):
        """Carregue corretamente se a string for JSON com aspas duplas."""
        categorias_str = '[{"categoria_id": 1, "nome": "X"}, {"categoria_id": 2, "nome": "Y"}]'
        result = _parse_marca(categorias_str)
        self.assertEqual(result, "Y")

    def test_parse_marca_list_object(self):
        """If pandas gives us a list directly, handle it."""
        categorias_val = [{'categoria_id': 101, 'nome': 'A'}, {'categoria_id': 102, 'nome': 'B'}]
        result = _parse_marca(categorias_val)
        self.assertEqual(result, "B")

    def test_parse_marca_dict_input(self):
        """If the column contains a single dict rather than a list."""
        result = _parse_marca({'nome': 'SINGLE'})
        self.assertEqual(result, "SINGLE")


class TestConvertFile(unittest.TestCase):
    """Tests for the convert_file function."""

    def setUp(self):
        """Set up temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_convert_single_product(self):
        """Test converting a file with a single product."""
        # create input file
        input_path = Path(self.test_dir) / "input.xlsx"
        data = {
            "codigo": ["12345"],
            "nome": ["Test Product"],
            "unidade": ["UN"],
            "saldo_estoque": [10],
            "preco": [100.00],
            "informacoes_adicionais": ["Test info"],
            "imagens": ["['https://example.com/img1.jpg']"],
            "categorias": ["[{'nome': 'CAT1'}, {'nome': 'TEST_BRAND'}]"],
        }
        df = pd.DataFrame(data)
        df.to_excel(input_path, index=False)

        # convert
        output_path = Path(self.test_dir) / "output.xlsx"
        convert_file(input_path, output_path)

        # verify output exists and has correct structure
        self.assertTrue(output_path.exists())
        result_df = pd.read_excel(output_path)

        # check key fields
        self.assertEqual(result_df["Código (SKU)"].iloc[0], "LEIRI12345")
        self.assertEqual(result_df["Descrição"].iloc[0], "Test Product")
        self.assertEqual(result_df["Unidade"].iloc[0], "UN")
        self.assertEqual(result_df["Estoque"].iloc[0], 10)
        self.assertEqual(result_df["Preço de custo"].iloc[0], 100.00)
        self.assertEqual(result_df["Situação"].iloc[0], "Ativo")
        self.assertEqual(result_df["Marca"].iloc[0], "TEST_BRAND")
        self.assertEqual(result_df["URL imagem 1"].iloc[0], "https://example.com/img1.jpg")

    def test_convert_multiple_products(self):
        """Test converting a file with multiple products."""
        input_path = Path(self.test_dir) / "input.xlsx"
        data = {
            "codigo": [1, 2, 3],
            "nome": ["Product 1", "Product 2", "Product 3"],
            "unidade": ["UN", "KG", "PC"],
            "saldo_estoque": [5, 10, 15],
            "preco": [50, 100, 150],
            "informacoes_adicionais": ["", "Info 2", ""],
            "imagens": ["[]", "['https://img.jpg']", "[]"],
            "categorias": ["[]", "[]", "[]"],
        }
        df = pd.DataFrame(data)
        df.to_excel(input_path, index=False)

        output_path = Path(self.test_dir) / "output.xlsx"
        convert_file(input_path, output_path)

        result_df = pd.read_excel(output_path)
        self.assertEqual(len(result_df), 3)
        self.assertEqual(list(result_df["Código (SKU)"]), ["LEIRI1", "LEIRI2", "LEIRI3"])

    def test_output_has_all_headers(self):
        """Test that output file contains all required headers."""
        input_path = Path(self.test_dir) / "input.xlsx"
        data = {
            "codigo": ["123"],
            "nome": ["Test"],
            "unidade": ["UN"],
            "saldo_estoque": [1],
            "preco": [10],
            "informacoes_adicionais": [""],
            "imagens": ["[]"],
            "categorias": ["[]"],
        }
        df = pd.DataFrame(data)
        df.to_excel(input_path, index=False)

        output_path = Path(self.test_dir) / "output.xlsx"
        convert_file(input_path, output_path)

        result_df = pd.read_excel(output_path)
        expected_headers = [
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
        self.assertEqual(list(result_df.columns), expected_headers)

    def test_default_values(self):
        """Test that default constant values are set correctly."""
        input_path = Path(self.test_dir) / "input.xlsx"
        data = {
            "codigo": ["999"],
            "nome": ["Default Test"],
            "unidade": ["UN"],
            "saldo_estoque": [0],
            "preco": [0],
            "informacoes_adicionais": [""],
            "imagens": ["[]"],
            "categorias": ["[]"],
        }
        df = pd.DataFrame(data)
        df.to_excel(input_path, index=False)

        output_path = Path(self.test_dir) / "output.xlsx"
        convert_file(input_path, output_path)

        result_df = pd.read_excel(output_path)
        row = result_df.iloc[0]

        # check default constants
        self.assertEqual(row["Origem"], "2 - Estrangeira - Adquirida no mercado interno, exceto a indicada no código 7")
        self.assertEqual(row["Valor IPI fixo"], 0)
        self.assertEqual(row["Situação"], "Ativo")
        self.assertEqual(row["Fornecedor"], "CICLO LEIRIENSE PECAS E ACESSORIOS PARA BICICLETAS LTDA")
        self.assertEqual(row["Estoque máximo"], 0)
        self.assertEqual(row["Estoque mínimo"], 1)
        self.assertEqual(row["Formato embalagem"], "Pacote / Caixa")
        self.assertEqual(row["Tipo do produto"], "S")
        self.assertEqual(row["Garantia"], "3 meses")
        self.assertEqual(row["Sob encomenda"], "Não")
        self.assertEqual(row["Dias para preparação"], 0)
        self.assertEqual(row["Controlar lotes"], "Não")
        self.assertEqual(row["Markup"], 0)
        self.assertEqual(row["Permitir inclusão nas vendas"], "Sim")

    def test_multiple_images_handling(self):
        """Test that multiple images are correctly distributed to image columns."""
        input_path = Path(self.test_dir) / "input.xlsx"
        data = {
            "codigo": ["456"],
            "nome": ["Multi Image"],
            "unidade": ["UN"],
            "saldo_estoque": [1],
            "preco": [50],
            "informacoes_adicionais": [""],
            "imagens": ["['https://img1.jpg', 'https://img2.jpg', 'https://img3.jpg', 'https://img4.jpg', 'https://img5.jpg', 'https://img6.jpg', 'https://img7.jpg']"],
            "categorias": ["[]"],
        }
        df = pd.DataFrame(data)
        df.to_excel(input_path, index=False)

        output_path = Path(self.test_dir) / "output.xlsx"
        convert_file(input_path, output_path)

        result_df = pd.read_excel(output_path)
        row = result_df.iloc[0]

        # should only have first 6 images
        self.assertEqual(row["URL imagem 1"], "https://img1.jpg")
        self.assertEqual(row["URL imagem 2"], "https://img2.jpg")
        self.assertEqual(row["URL imagem 3"], "https://img3.jpg")
        self.assertEqual(row["URL imagem 4"], "https://img4.jpg")
        self.assertEqual(row["URL imagem 5"], "https://img5.jpg")
        self.assertEqual(row["URL imagem 6"], "https://img6.jpg")
        # 7th image should not be in any column
        self.assertNotIn("https://img7.jpg", row.values)


if __name__ == "__main__":
    unittest.main()
