import requests
import json
import csv
import os
import subprocess
import shutil
import tempfile
import zipfile
import urllib.request
import urllib.error
import platform
import hashlib
from datetime import datetime
from pathlib import Path
import time

class GitHubAnalyzer:
    def __init__(self, token):
        """
        Inicializa o analisador com token de acesso do GitHub
        """

        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://api.github.com/graphql"
        # Usa nomes de pasta muito curtos para evitar problemas de path no Windows
        if platform.system() == "Windows":
            self.temp_dir = "t"  # Nome super curto no Windows
        else:
            self.temp_dir = "temp"
        self.ck_jar_path = "ck/target/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar"
    
    def create_graphql_query(self, cursor=None):
        """
        Cria a query GraphQL para buscar os repositórios mais populares
        """

        after_clause = f', after: "{cursor}"' if cursor else ""
        
        query = f"""
        query {{
            search(query: "stars:>1000 language:java", type: REPOSITORY, first: 20{after_clause}) {{
                pageInfo {{
                    hasNextPage
                    endCursor
                }}
                nodes {{
                    ... on Repository {{
                        name
                        owner {{
                            login
                        }}
                        stargazerCount
                        createdAt
                        primaryLanguage {{
                            name
                        }}
                        releases {{
                            totalCount
                        }}
                        url
                        description
                    }}
                }}
            }}
        }}
        """
        return query
    
    def make_request(self, query):
        """
        Faz a requisição GraphQL para a API do GitHub
        """

        payload = {"query": query}
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                print("ERRO: Token inválido ou expirado!")
                print("Verifique se seu token GitHub está correto e tem as permissões necessárias.")
                return None
            elif response.status_code == 403:
                print("ERRO: Rate limit atingido ou permissões insuficientes!")
                print("Aguarde alguns minutos ou verifique as permissões do token.")
                return None
            elif response.status_code >= 500:
                print(f"ERRO: Problema temporário no servidor GitHub (Código {response.status_code})")
                print("Tente novamente em alguns minutos.")
                return None
            else:
                print(f"Erro na requisição: {response.status_code}")
                print(f"Resposta: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Erro de conexão: {e}")
            return None
    
    def calculate_age_days(self, created_at):
        """
        Calcula a idade do repositório em dias
        """

        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        current_date = datetime.now(created_date.tzinfo)
        return (current_date - created_date).days

    def process_repository_data(self, repo):
        """
        Processa os dados de um repositório individual
        """

        return {
            'name': repo['name'],
            'owner': repo['owner']['login'],
            'url': repo['url'],
            'description': repo['description'] or "",
            'stars': repo['stargazerCount'],
            'age_days': self.calculate_age_days(repo['createdAt']),
            'primary_language': repo['primaryLanguage']['name'] if repo['primaryLanguage'] else "Unknown",
            'total_releases': repo['releases']['totalCount'],
            'created_at': repo['createdAt']
        }
    
    def collect_repositories_data(self, limit=100):
        """
        Coleta dados dos repositórios mais populares
        """

        repositories = []
        cursor = None
        collected = 0
        
        print(f"Iniciando coleta de dados para {limit} repositórios...")
        
        while collected < limit:
            query = self.create_graphql_query(cursor)
            response_data = self.make_request(query)
            
            if not response_data or 'data' not in response_data:
                print("Erro ao obter dados da API")
                break
            
            search_results = response_data['data']['search']
            repos = search_results['nodes']
            
            for repo in repos:
                if collected >= limit:
                    break
                    
                try:
                    processed_repo = self.process_repository_data(repo)
                    repositories.append(processed_repo)
                    collected += 1
                    
                    if collected % 20 == 0:
                        print(f"Coletados {collected}/{limit} repositórios... ({(collected/limit)*100:.1f}%)")
                        
                except Exception as e:
                    print(f"Erro ao processar repositório {repo.get('name', 'Unknown')}: {e}")
                    continue
            
            if not search_results['pageInfo']['hasNextPage'] or collected >= limit:
                break
                
            cursor = search_results['pageInfo']['endCursor']
            
            time.sleep(3)
        
        print(f"Coleta finalizada. Total coletado: {len(repositories)} repositórios")
        return repositories
    
    def download_repository_zip(self, repo_url, repo_name):
        """
        Baixa o repositório como ZIP e descompacta (muito mais rápido que git clone)
        """
        clone_path = os.path.join(self.temp_dir, repo_name)
        
        try:
            # Limpa o diretório temporário completamente para evitar conflitos
            if os.path.exists(self.temp_dir):
                for item in os.listdir(self.temp_dir):
                    item_path = os.path.join(self.temp_dir, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
            else:
                os.makedirs(self.temp_dir, exist_ok=True)
            
            # Converte URL do repositório para URL do ZIP
            if repo_url.endswith('.git'):
                repo_url = repo_url[:-4]  # Remove .git
            zip_url = f"{repo_url}/archive/refs/heads/main.zip"
            
            print(f"Baixando ZIP: {zip_url}")
            
            # Baixa o arquivo ZIP
            zip_path = os.path.join(self.temp_dir, f"{repo_name}.zip")
            
            # Configura headers para evitar rate limiting
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'
            
            req = urllib.request.Request(zip_url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=120) as response:
                if response.status == 200:
                    with open(zip_path, 'wb') as f:
                        shutil.copyfileobj(response, f)
                    print(f"ZIP baixado com sucesso ({os.path.getsize(zip_path) / 1024 / 1024:.1f} MB)")
                else:
                    print(f"Erro ao baixar ZIP: HTTP {response.status}")
                    return None
            
            # Descompacta o ZIP com estratégia otimizada para Windows
            print(f"Descompactando ZIP...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                if platform.system() == "Windows":
                    # Extração seletiva no Windows para evitar caminhos longos
                    for member in zip_ref.infolist():
                        try:
                            # Calcula tamanho total do caminho
                            full_path = os.path.join(self.temp_dir, member.filename)
                            
                            # Pula arquivos com caminhos muito longos
                            if len(full_path) > 220:
                                continue
                            
                            # Pula arquivos com nomes muito longos
                            if len(member.filename) > 180:
                                continue
                            
                            # Pula arquivos com muitos níveis de diretório
                            if member.filename.count('/') > 12:
                                continue
                            
                            # Pula arquivos com caracteres problemáticos
                            problematic_chars = ['<', '>', ':', '"', '|', '?', '*']
                            if any(char in member.filename for char in problematic_chars):
                                continue
                            
                            # Extrai apenas arquivos relevantes para análise Java
                            if not member.is_dir():
                                file_ext = os.path.splitext(member.filename)[1].lower()
                                # Prioriza arquivos Java e alguns outros importantes
                                if file_ext not in ['.java', '.xml', '.properties', '.gradle', '.pom', '.kt', '.scala', '']:
                                    continue
                            
                            zip_ref.extract(member, self.temp_dir)
                            
                        except Exception as e:
                            # Continua mesmo se der erro em arquivos específicos
                            continue
                else:
                    # Extração completa em sistemas não-Windows
                    zip_ref.extractall(self.temp_dir)
            
            # Remove o arquivo ZIP
            os.remove(zip_path)
            
            # Encontra o diretório extraído
            print(f"Procurando diretório extraído para: {repo_name}")
            
            # Lista todos os diretórios para debug
            all_dirs = [d for d in os.listdir(self.temp_dir) 
                       if os.path.isdir(os.path.join(self.temp_dir, d))]
            print(f"Diretórios encontrados: {all_dirs}")
            
            # Busca o diretório correto com várias estratégias
            extracted_path = None
            
            # Estratégia 1: nome exato com sufixos comuns
            repo_clean = repo_name.replace('_', '-')  # krahets_hello-algo -> krahets-hello-algo
            possible_names = [
                f"{repo_clean}-main",
                f"{repo_clean}-master", 
                f"{repo_clean}-develop",
                repo_clean,
                repo_name
            ]
            
            for possible in possible_names:
                if possible in all_dirs:
                    extracted_path = os.path.join(self.temp_dir, possible)
                    print(f"Encontrado por nome exato: {possible}")
                    break
            
            # Estratégia 2: busca por substring se não encontrou exato
            if not extracted_path:
                repo_parts = repo_name.split('_')
                if len(repo_parts) >= 2:
                    owner, name = repo_parts[0], repo_parts[1]
                    for dir_name in all_dirs:
                        if name in dir_name and (owner in dir_name or 'main' in dir_name or 'master' in dir_name):
                            extracted_path = os.path.join(self.temp_dir, dir_name)
                            print(f"Encontrado por substring: {dir_name}")
                            break
            
            # Estratégia 3: busca por partes do nome do repo
            if not extracted_path:
                repo_parts = repo_name.split('_')
                if len(repo_parts) >= 2:
                    owner, name = repo_parts[0], repo_parts[1]
                    for dir_name in all_dirs:
                        # Procura diretórios que contenham o nome do repositório
                        if name.lower() in dir_name.lower():
                            extracted_path = os.path.join(self.temp_dir, dir_name)
                            print(f"Encontrado por nome do repo: {dir_name}")
                            break
            
            # Estratégia 4: pega o primeiro diretório se só tem um
            if not extracted_path and len(all_dirs) == 1:
                extracted_path = os.path.join(self.temp_dir, all_dirs[0])
                print(f"Único diretório encontrado: {all_dirs[0]}")
                
            # Estratégia 5: pega qualquer diretório que não seja oculto
            if not extracted_path:
                non_hidden_dirs = [d for d in all_dirs if not d.startswith('.')]
                if non_hidden_dirs:
                    extracted_path = os.path.join(self.temp_dir, non_hidden_dirs[0])
                    print(f"Primeiro diretório não oculto: {non_hidden_dirs[0]}")
            
            if extracted_path and os.path.exists(extracted_path):
                # Renomeia para o nome esperado
                if extracted_path != clone_path:
                    os.rename(extracted_path, clone_path)
                
                print(f"Repositório extraído e renomeado para: {clone_path}")
                return clone_path
            else:
                print(f"Erro: Diretório extraído não encontrado")
                print(f"   Esperado: alguma variação de '{repo_name}'")
                print(f"   Encontrados: {all_dirs}")
                return None
                
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Tenta com master ao invés de main
                try:
                    zip_url_master = f"{repo_url}/archive/refs/heads/master.zip"
                    print(f"Tentando com branch master: {zip_url_master}")
                    
                    req = urllib.request.Request(zip_url_master, headers=headers)
                    with urllib.request.urlopen(req, timeout=120) as response:
                        if response.status == 200:
                            with open(zip_path, 'wb') as f:
                                shutil.copyfileobj(response, f)
                            
                            # Descompacta com mesma estratégia otimizada
                            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                                if platform.system() == "Windows":
                                    for member in zip_ref.infolist():
                                        try:
                                            full_path = os.path.join(self.temp_dir, member.filename)
                                            if (len(full_path) > 220 or len(member.filename) > 180 or
                                                member.filename.count('/') > 8 or
                                                any(char in member.filename for char in ['<', '>', ':', '"', '|', '?', '*'])):
                                                continue
                                            if not member.is_dir():
                                                file_ext = os.path.splitext(member.filename)[1].lower()
                                                if file_ext not in ['.java', '.xml', '.properties', '.gradle', '.pom', '.kt', '.scala', '']:
                                                    continue
                                            zip_ref.extract(member, self.temp_dir)
                                        except Exception:
                                            continue
                                else:
                                    zip_ref.extractall(self.temp_dir)
                            os.remove(zip_path)
                            
                            # Aplica a mesma lógica de detecção de diretório
                            all_dirs = [d for d in os.listdir(self.temp_dir) 
                                       if os.path.isdir(os.path.join(self.temp_dir, d))]
                            
                            extracted_path = None
                            repo_clean = repo_name.replace('_', '-')
                            possible_names = [
                                f"{repo_clean}-master",
                                f"{repo_clean}-main", 
                                repo_clean,
                                repo_name
                            ]
                            
                            for possible in possible_names:
                                if possible in all_dirs:
                                    extracted_path = os.path.join(self.temp_dir, possible)
                                    break
                            
                            if not extracted_path and len(all_dirs) == 1:
                                extracted_path = os.path.join(self.temp_dir, all_dirs[0])
                            
                            if extracted_path and os.path.exists(extracted_path):
                                if extracted_path != clone_path:
                                    os.rename(extracted_path, clone_path)
                                print(f"Repositório baixado com branch master")
                                return clone_path
                            
                except Exception:
                    pass
            
            print(f"Erro HTTP ao baixar ZIP: {e.code} - {e.reason}")
            return None
            
        except Exception as e:
            print(f"Erro ao baixar repositório {repo_url}: {e}")
            return None
    
    def run_ck_analysis(self, repo_path):
        """
        Executa análise CK no repositório clonado
        """
        try:
            if not os.path.exists(self.ck_jar_path):
                print(f"Arquivo CK não encontrado: {self.ck_jar_path}")
                return None
            
            # Garante que a pasta temp existe (usa nome dependente do OS)
            if platform.system() == "Windows":
                temp_csv_path = "t"
            else:
                temp_csv_path = "temp"
            os.makedirs(temp_csv_path, exist_ok=True)
            
            print(f"Executando análise CK em: {repo_path}")
            
            # Comando para executar CK
            cmd = [
                "java", "-jar", self.ck_jar_path,
                repo_path,
                "true",  # usar diretórios
                "0",     # máximo arquivos
                "true",  # usar jarfiles
                temp_csv_path + "/"
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=os.getcwd(),
                timeout=300  # 5 minutos timeout
            )
            
            if result.returncode == 0:
                print("Análise CK concluída com sucesso")
                return self.parse_ck_results_from_temp(temp_csv_path)
            else:
                print(f"Erro na análise CK: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("Timeout na análise CK")
            return None
        except Exception as e:
            print(f"Erro ao executar CK: {e}")
            return None
    
    def parse_ck_results_from_temp(self, temp_csv_path=None):
        """
        Parse dos resultados do CK da pasta temp/
        """
        if temp_csv_path is None:
            if platform.system() == "Windows":
                temp_path = "t"
            else:
                temp_path = "temp"
        else:
            temp_path = temp_csv_path
        
        try:
            # Arquivos CK gerados na pasta temp/
            class_csv = os.path.join(temp_path, "class.csv")
            
            metrics = {
                'total_classes': 0,
                'total_methods': 0,
                'total_fields': 0,
                'total_variables': 0,
                'avg_wmc': 0,
                'cbo': 0,
                'lcom': 0,
                'dit': 0,
                'avg_noc': 0,
                'avg_rfc': 0,
                'loc': 0,
                'avg_cc': 0
            }
            
            print(f"Extraindo métricas dos arquivos CSV...")
            
            # Parse class metrics
            if os.path.exists(class_csv):
                print(f"Processando {class_csv}")
                with open(class_csv, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    classes = list(reader)
                    metrics['total_classes'] = len(classes)
                    
                    if classes:
                        metrics['cbo'] = sum(float(c.get('cbo', 0)) for c in classes)
                        metrics['lcom'] = sum(float(c.get('lcom', 0)) for c in classes)
                        metrics['dit'] = sum(float(c.get('dit', 0)) for c in classes)
                        metrics['loc'] = sum(float(c.get('loc', 0)) for c in classes)
            
            # Limpa arquivos CSV da pasta temp
            self.cleanup_temp_csv_files(temp_path)
            
            print(f"Métricas extraídas: {metrics['total_classes']} classes")
            return metrics
            
        except Exception as e:
            print(f"Erro ao parsear resultados CK: {e}")
            # Tenta limpar arquivos mesmo em caso de erro
            self.cleanup_temp_csv_files(temp_path)
            return None
    
    def cleanup_temp_csv_files(self, temp_path=None):
        """
        Remove arquivos CSV da pasta temp após extrair métricas
        """
        if temp_path is None:
            if platform.system() == "Windows":
                temp_path = "t"
            else:
                temp_path = "temp"
        csv_files = ["class.csv", "method.csv", "field.csv", "variable.csv"]
        
        for csv_file in csv_files:
            file_path = os.path.join(temp_path, csv_file)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Removido: {csv_file}")
            except Exception as e:
                print(f"Erro ao remover {csv_file}: {e}")
    
    def process_single_repository(self, repo):
        """
        Processa um único repositório: clona, executa CK e retorna métricas
        """
        # Usa nomes muito curtos para evitar problemas de path no Windows
        if platform.system() == "Windows":
            # Gera nome curto baseado em hash
            repo_id = f"{repo['owner']}/{repo['name']}"
            short_name = hashlib.md5(repo_id.encode()).hexdigest()[:8]
            repo_name = short_name
        else:
            repo_name = f"{repo['owner']}_{repo['name']}"
        
        clone_url = f"https://github.com/{repo['owner']}/{repo['name']}.git"
        
        print(f"\nProcessando repositório: {repo['owner']}/{repo['name']}")
        if platform.system() == "Windows":
            print(f"Nome da pasta temporária: {repo_name}")
        
        # Baixa repositório como ZIP (mais rápido que git clone)
        repo_path = self.download_repository_zip(clone_url, repo_name)
        if not repo_path:
            return None
        
        try:
            # Executa análise CK
            ck_metrics = self.run_ck_analysis(repo_path)
            
            if ck_metrics:
                # Combina dados do repositório com métricas CK
                result = {
                    'name': repo['name'],
                    'owner': repo['owner'],
                    'url': repo['url'],
                    'description': repo['description'],
                    'stars': repo['stars'],
                    'age_days': repo['age_days'],
                    'primary_language': repo['primary_language'],
                    'total_releases': repo['total_releases'],
                    'created_at': repo['created_at'],
                    **ck_metrics
                }
                
                # Limpa repositório imediatamente após análise bem-sucedida
                print(f"Análise CK concluída. Removendo repositório clonado...")
                self.cleanup_repo(repo_path)
                
                return result
            else:
                print(f"Falha na análise CK para {repo_name}")
                # Limpa repositório mesmo em caso de falha
                print(f"Removendo repositório clonado...")
                self.cleanup_repo(repo_path)
                return None
                
        except Exception as e:
            print(f"Erro durante processamento: {e}")
            # Limpa repositório em caso de erro
            print(f"Removendo repositório clonado...")
            self.cleanup_repo(repo_path)
            return None
    
    def append_to_csv(self, repo_data, filename="repositories_ck_analysis.csv"):
        """
        Adiciona uma linha ao CSV (para processamento incremental)
        """
        fieldnames = [
            'name', 'owner', 'url', 'description', 'stars',
            'age_days', 'primary_language', 'total_releases', 'created_at',
            'total_classes', 'total_methods', 'total_fields', 'total_variables',
            'avg_wmc', 'cbo', 'lcom', 'dit', 'avg_noc', 'avg_rfc',
            'loc', 'avg_cc'
        ]
        
        file_exists = os.path.exists(filename)
        
        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(repo_data)
        
        print(f"Dados de {repo_data['owner']}/{repo_data['name']} adicionados ao CSV")
    
    def analyze_repositories_with_ck(self, limit=1000):
        """
        Coleta TODOS os repositórios primeiro, depois processa um por um com CK
        """
        csv_filename = "repositories_ck_analysis.csv"
        
        # PRIMEIRO: Remove CSV antigo se existir
        if os.path.exists(csv_filename):
            try:
                os.remove(csv_filename)
                print(f"CSV antigo removido: {csv_filename}")
            except Exception as e:
                print(f"Erro ao remover CSV antigo: {e}")
        
        print(f"Iniciando coleta de repositórios...")
        
        # SEGUNDO: Coleta TODOS os dados dos repositórios
        repositories = self.collect_repositories_data(limit)
        
        if not repositories:
            print("Nenhum repositório encontrado")
            return []
        
        print(f"\n{'='*60}")
        print(f"COLETA FINALIZADA!")
        print(f"Total de repositórios coletados: {len(repositories)}")
        print(f"Dados completos salvos na variável 'repositories'")
        print(f"{'='*60}")
        
        # Exibe resumo dos repositórios coletados
        print("\nRepositórios que serão analisados:")
        for i, repo in enumerate(repositories, 1):
            print(f"{i:3d}. {repo['owner']}/{repo['name']} ({repo['stars']:,})")
        
        print(f"\n{'='*60}")
        print("INICIANDO ANÁLISE CK...")
        print(f"{'='*60}")
        
        processed_repos = []
        
        # SEGUNDO: Processa cada repositório com CK (um por vez)
        for i, repo in enumerate(repositories, 1):
            print(f"\n{'='*60}")
            print(f"ANALISANDO {i}/{len(repositories)}: {repo['owner']}/{repo['name']}")
            print(f"URL: {repo['url']}")
            print(f"Stars: {repo['stars']:,} | Linguagem: {repo['primary_language']}")
            print(f"{'='*60}")
            
            # Processa repositório individual
            result = self.process_single_repository(repo)
            
            if result:
                # Adiciona ao CSV imediatamente
                self.append_to_csv(result, csv_filename)
                processed_repos.append(result)
                print(f"Repositório processado com sucesso")
            else:
                print(f"Falha no processamento do repositório")
                
            
            # Pausa entre repositórios para evitar sobrecarga
            if i < len(repositories):
                print("Aguardando 3 segundos...")
                time.sleep(3)
        
        print(f"\n{'='*60}")
        print(f"ANÁLISE CK FINALIZADA!")
        print(f"Repositórios processados com sucesso: {len(processed_repos)}/{len(repositories)}")
        print(f"Resultados salvos em: {csv_filename}")
        print(f"{'='*60}")
        
        return processed_repos
    
    def cleanup_repo(self, repo_path):
        """
        Remove um repositório específico imediatamente
        """
        try:
            if repo_path and os.path.exists(repo_path):
                shutil.rmtree(repo_path)
                print(f"Repositório removido: {os.path.basename(repo_path)}")
                return True
        except Exception as e:
            print(f"Erro ao remover repositório {repo_path}: {e}")
            return False
    
    def cleanup(self):
        """
        Limpa diretório temporário completo
        """
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print(f"Diretório temporário removido: {self.temp_dir}")
        except Exception as e:
            print(f"Erro ao limpar diretório temporário: {e}")
    
    def print_summary(self, repositories):
        """
        Imprime um resumo dos dados coletados
        """

        if not repositories:
            return
        
        print("\n" + "="*50)
        print("RESUMO DOS DADOS COLETADOS")
        print("="*50)
        
        print(f"Total de repositórios: {len(repositories)}")
        
        ages = [repo['age_days'] for repo in repositories]
        stars = [repo['stars'] for repo in repositories]
        releases = [repo['total_releases'] for repo in repositories]
        
        print(f"\nIdade dos repositórios:")
        print(f"  Mediana: {sorted(ages)[len(ages)//2]} dias")
        print(f"  Média: {sum(ages)/len(repositories):.1f} dias")
        print(f"  Mínima: {min(ages)} dias")
        print(f"  Máxima: {max(ages)} dias")
        
        print(f"\nEstrelas:")
        print(f"  Mediana: {sorted(stars)[len(stars)//2]:,}")
        print(f"  Média: {sum(stars)/len(repositories):.1f} dias")
        print(f"  Mínima: {min(stars):,}")
        print(f"  Máxima: {max(stars):,}")

        print(f"\nReleases:")
        print(f"  Mediana: {sorted(releases)[len(releases)//2]:,}")
        print(f"  Média: {sum(releases)/len(repositories):.1f}")
        print(f"  Máximo: {max(releases):,}")

def load_env_file():
    """
    Carrega variáveis de ambiente de um arquivo .env (opcional)
    """

    try:
        if os.path.exists('.env'):
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
    except Exception as e:
        pass


def main():
    """
    Função principal do programa
    """

    load_env_file()
    
    token = os.getenv('GITHUB_TOKEN')
    
    if not token:
        print("ERRO: Token do GitHub não encontrado!")
        return

    analyzer = GitHubAnalyzer(token)
    
    try:
        # Processa repositórios com análise CK (um por vez)
        processed_repos = analyzer.analyze_repositories_with_ck(limit=1000)
        
        if processed_repos:
            print(f"\n{'='*60}")
            print("RESUMO DA ANÁLISE CK")
            print(f"{'='*60}")
            print(f"Repositórios analisados: {len(processed_repos)}")
            
            if processed_repos:
                # Estatísticas das métricas CK
                stars = [r.get('stars', 0) for r in processed_repos if r.get('stars')]
                loc = [r.get('loc', 0) for r in processed_repos if r.get('loc')]
                releases = [r.get('releases', 0) for r in processed_repos if r.get('releases')]
                age = [r.get('age_days', 0) for r in processed_repos if r.get('age_days')]

                cbo = [r.get('cbo', 0) for r in processed_repos if r.get('cbo')]
                dit = [r.get('dit', 0) for r in processed_repos if r.get('dit')]
                lcom = [r.get('lcom', 0) for r in processed_repos if r.get('lcom')]

                
                
                print('Métricas de processo:  \n')

                if stars:
                    print(f"Média de estrelas por repositório: {sum(stars)/len(processed_repos):.1f}")
                if loc:
                    print(f"Média de linhas de código: {sum(loc)/len(processed_repos):.2f}")
                if releases:
                    print(f"Média de atividade: {sum(releases)/len(processed_repos):.2f}")
                if age:
                    print(f"Média de maturidade: {sum(age)/len(processed_repos):.2f}")

                print('\n ---------------------------------------- \n')


                print('Métricas de qualidade:  \n')

                if cbo:
                    print(f"CBO Médio: {sum(cbo)/len(processed_repos):.2f}")
                if dit:
                    print(f"DIT Médio: {sum(dit)/len(processed_repos):.2f}")

                if lcom:
                    print(f"LCOM Médio: {sum(lcom)/len(processed_repos):.2f}")

        else:
            print("Nenhum repositório foi processado com sucesso.")
    
    except KeyboardInterrupt:
        print("\n\nInterrompido pelo usuário.")
    except Exception as e:
        print(f"\nErro durante a execução: {e}")
    finally:
        # Limpa diretório temporário
        analyzer.cleanup()


if __name__ == "__main__":
    main()
