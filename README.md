# Análise de Qualidade de Software em Repositórios Java

## Descrição

Este projeto coleta repositórios Java populares do GitHub e executa análise de qualidade de código usando a ferramenta CK (Code Quality metrics). O sistema analisa métricas de qualidade como complexidade, acoplamento, coesão e outras características importantes de software.

## Pré-requisitos

### 1. Java JDK 8+
Instale o Java Development Kit:

**Windows:**
1. Baixe o JDK em: https://www.oracle.com/java/technologies/downloads/
2. Execute o instalador
3. Configure a variável `JAVA_HOME`:
   - Painel de Controle → Sistema → Configurações Avançadas → Variáveis de Ambiente
   - Nova variável: `JAVA_HOME` = `C:\Program Files\Java\jdk-XX`
   - Adicione `%JAVA_HOME%\bin` ao PATH

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install openjdk-11-jdk
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
```

**macOS:**
```bash
# Homebrew
brew install openjdk@11
export JAVA_HOME=$(/usr/libexec/java_home -v 11)
```

Verifique a instalação:
```bash
java -version
javac -version
```

### 2. Apache Maven 3.6+
Instale o Maven para compilar o CK:

**Windows:**
1. Baixe em: https://maven.apache.org/download.cgi
2. Extraia para `C:\Program Files\Apache\maven`
3. Adicione `C:\Program Files\Apache\maven\bin` ao PATH

**Linux (Ubuntu/Debian):**
```bash
sudo apt install maven
```

**macOS:**
```bash
brew install maven
```

Verifique a instalação:
```bash
mvn -version
```

### 3. Git
Certifique-se que o Git está instalado:

**Windows:** https://git-scm.com/download/win
**Linux:** `sudo apt install git`
**macOS:** `brew install git`

### 4. Python 3.7+
Certifique-se que o Python está instalado:
```bash
python --version
```

## Configuração do Projeto

### 1. Clone e Configure o CK
```bash
# Clone o repositório CK
git clone https://github.com/mauricioaniche/ck.git

# Entre no diretório
cd ck

# Compile o projeto
mvn clean compile assembly:single

# Volte para o diretório principal
cd ..
```

Isso criará o arquivo: `ck/target/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar`

### 2. Token do GitHub
Configure um token pessoal do GitHub:

#### Gerar Token:
1. Acesse: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Clique em "Generate new token (classic)"
3. Selecione as permissões necessárias:
   - `public_repo` (para acessar repositórios públicos)
   - `read:org` (para organizações)
4. Copie o token gerado

#### Configurar Token:

**Opção 1 - Arquivo .env (recomendado):**
1. Crie um arquivo `.env` na raiz do projeto
2. Adicione a linha: `GITHUB_TOKEN=seu_token_aqui`

Exemplo do arquivo `.env`:
```
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Opção 2 - Variável de Ambiente:**
```bash
# Windows (cmd)
set GITHUB_TOKEN=seu_token_aqui

# Windows (PowerShell)
$env:GITHUB_TOKEN='seu_token_aqui'

# Linux/Mac
export GITHUB_TOKEN=seu_token_aqui
```

### 3. Dependências Python
Instale as dependências do projeto:

```bash
# Windows
py -m pip install -r requirements.txt

# Linux/Mac
pip install -r requirements.txt
```

Dependências utilizadas:
- `requests` - Para requisições HTTP à API do GitHub

### 4. Estrutura de Diretórios
Certifique-se que a estrutura está assim:
```
projeto/
├── main.py
├── requirements.txt
├── .env
├── ck/
│   └── target/
│       └── ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar
└── temp/ (será criado automaticamente)
```

## Execução

```bash
# Windows
py main.py

# Linux/Mac
python main.py
```

### Fluxo de Execução:
1. **Coleta repositórios** - Busca os repositórios Java mais populares no GitHub
2. **Para cada repositório**:
   - Baixa o repositório como ZIP (muito mais rápido que git clone)
   - Descompacta o ZIP
   - Executa análise CK
   - Extrai métricas dos arquivos CSV
   - Remove arquivos temporários
   - Salva resultado no CSV final

## Dados Coletados

### Informações do Repositório (GitHub API)
- **name** - Nome do repositório
- **owner** - Proprietário/organização
- **url** - URL do repositório
- **description** - Descrição
- **stars** - Número de estrelas
- **age_days** - Idade em dias
- **primary_language** - Linguagem principal
- **total_releases** - Total de releases
- **created_at** - Data de criação

### Métricas de Qualidade (CK Tool) (TODO: Conferir como pegar certinho)
- **total_classes** - Total de classes
- **total_methods** - Total de métodos
- **total_fields** - Total de campos
- **total_variables** - Total de variáveis
- **avg_wmc** - WMC médio (Weighted Method Count)
- **avg_cbo** - CBO médio (Coupling Between Objects)
- **avg_lcom** - LCOM médio (Lack of Cohesion of Methods)
- **avg_dit** - DIT médio (Depth of Inheritance Tree)
- **avg_noc** - NOC médio (Number of Children)
- **avg_rfc** - RFC médio (Response for Class)
- **avg_loc** - LOC médio (Lines of Code)
- **avg_cc** - CC médio (Cyclomatic Complexity)

## Saída

O script gera:
1. **Arquivo CSV**: `repositories_ck_analysis.csv` com dados dos repositórios analisados
2. **Logs detalhados** no terminal com progresso da análise
3. **Pasta temp/** temporária com arquivos CSV do CK (removidos automaticamente)

### Exemplo de Saída no Terminal:
```
CSV antigo removido: repositories_ck_analysis.csv
Iniciando coleta de repositórios...

COLETA FINALIZADA!
Total de repositórios coletados: 5

Repositórios que serão analisados:
  1. spring-projects/spring-boot (70,234)
  2. elastic/elasticsearch (65,123)
  3. apache/kafka (25,456)

INICIANDO ANÁLISE CK...
ANALISANDO 1/5: spring-projects/spring-boot
URL: https://github.com/spring-projects/spring-boot
Stars: 70,234 | Linguagem: Java

Baixando ZIP: https://github.com/spring-projects/spring-boot/archive/refs/heads/main.zip
ZIP baixado com sucesso (45.2 MB)
Descompactando ZIP...
Repositório baixado e extraído em: /temp/spring-projects_spring-boot
Executando análise CK em: /temp/spring-projects_spring-boot
Análise CK concluída com sucesso
Extraindo métricas dos arquivos CSV...
Processando temp/class.csv
Processando temp/method.csv
Processando temp/field.csv
Processando temp/variable.csv
Removido: class.csv
Removido: method.csv
Removido: field.csv
Removido: variable.csv
Métricas extraídas: 2,456 classes, 18,932 métodos
Análise CK concluída. Removendo repositório clonado...
Repositório removido: spring-projects_spring-boot
Dados de spring-projects/spring-boot adicionados ao CSV
Repositório processado com sucesso
```

## Configuração Avançada

### Personalizar Limite de Repositórios
Edite o arquivo `main.py` na linha:
```python
processed_repos = analyzer.analyze_repositories_with_ck(limit=5)  # Altere aqui
```

### Filtros de Busca
O projeto busca repositórios com:
- Linguagem: Java
- Estrelas: > 1000
- Ordenação: Por popularidade (mais estrelas)

## Solução de Problemas

### Erro: "java: command not found"
- Verifique se o Java está instalado: `java -version`
- Configure a variável JAVA_HOME
- Adicione Java ao PATH

### Erro: "mvn: command not found" 
- Instale o Apache Maven
- Adicione Maven ao PATH

### Erro: "CK JAR não encontrado"
- Compile o projeto CK: `mvn clean compile assembly:single`
- Verifique se o arquivo existe: `ck/target/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar`

### Erro: "GitHub API rate limit"
- Verifique se o token está configurado corretamente
- Use um token com permissões adequadas
- Aguarde reset do rate limit (1 hora)

### Erro: "Erro ao baixar ZIP"
- Verifique conexão com internet
- Repositório pode estar privado ou removido
- Verifique se o token GitHub tem permissões adequadas
- Alguns repositórios podem usar branch 'master' ao invés de 'main' (o sistema tenta ambos automaticamente)

## Estrutura do CSV Final

O arquivo `repositories_ck_analysis.csv` contém uma linha por repositório com todas as métricas coletadas:

```csv
name,owner,url,description,stars,age_days,primary_language,total_releases,created_at,total_classes,total_methods,total_fields,total_variables,avg_wmc,avg_cbo,avg_lcom,avg_dit,avg_noc,avg_rfc,avg_loc,avg_cc
spring-boot,spring-projects,https://github.com/spring-projects/spring-boot,"Spring Boot",70234,2847,Java,152,2013-12-05T08:42:47Z,2456,18932,15423,45321,8.5,4.2,0.6,2.1,0.8,15.3,142.5,2.8
...
```