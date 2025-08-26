# Estudo das características de qualidade de sistemas Java

## Descrição

## Configuração

### 1. Token do GitHub
Antes de executar o script, você precisa gerar e configurar um token pessoal do GitHub:

#### Gerar Token:
1. Acesse: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Clique em "Generate new token (classic)"
3. Selecione as permissões necessárias:
   - `public_repo` (para acessar repositórios públicos)
   - `read:org` (para organizações)
4. Copie o token gerado

#### Configurar Token:

**Opção 1 - Variável de Ambiente:**
```bash
# Windows (cmd)
set GITHUB_TOKEN=seu_token_aqui
python main.py

# Windows (PowerShell)
$env:GITHUB_TOKEN='seu_token_aqui'
python main.py

# Linux/Mac
export GITHUB_TOKEN=seu_token_aqui
python main.py
```

**Opção 2 - Arquivo .env (recomendado):**
1. Crie um arquivo `.env` na raiz do projeto
2. Adicione a linha: `GITHUB_TOKEN=seu_token_aqui`
3. Execute normalmente: `python main.py`

Exemplo do arquivo `.env`:
```
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 2. Dependências
Instale as dependências do projeto:

```bash
# Windows
py -m pip install -r requirements.txt

# Linux/Mac
pip install -r requirements.txt
```

Dependências utilizadas:
- `requests` - Para requisições HTTP à API do GitHub
- `json`, `csv`, `os`, `datetime`, `time` - Bibliotecas padrão do Python

## Execução
```bash
# Windows
py main.py

# Linux/Mac
python main.py
```

## Dados Coletados

## Saída

O script gera:
1. **Arquivo CSV**: `repositories_1000_data.csv` com dados de 1.000 repositórios
2. **Resumo no terminal**: 

## Query GraphQL Utilizada

## Funcionalidades Implementadas

## Estrutura do CSV