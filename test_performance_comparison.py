#!/usr/bin/env python3
"""
Compara performance entre os diferentes métodos de carregamento
Mostra exatamente como o Metabase nativo é mais rápido
"""

import requests
import time
import statistics
import json
from tabulate import tabulate

class PerformanceComparator:
    def __init__(self):
        self.base_url = "http://localhost:8080/metabase_customizacoes"
        self.question_id = 51
        self.results = []
        
    def test_method(self, name, endpoint, runs=3):
        """Testa um método múltiplas vezes"""
        print(f"\n🧪 Testando {name}...")
        times = []
        row_counts = []
        
        for i in range(runs):
            print(f"   Run {i+1}/{runs}...", end='', flush=True)
            
            start = time.time()
            try:
                response = requests.get(
                    f"{self.base_url}{endpoint}?question_id={self.question_id}",
                    timeout=300
                )
                elapsed = time.time() - start
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Conta linhas baseado no formato
                    if isinstance(data, dict) and 'data' in data:
                        # Formato nativo
                        if 'rows' in data['data']:
                            rows = len(data['data']['rows'])
                        else:
                            rows = 0
                    elif isinstance(data, list):
                        # Formato array
                        rows = len(data)
                    else:
                        rows = 0
                    
                    times.append(elapsed)
                    row_counts.append(rows)
                    print(f" ✓ {elapsed:.2f}s ({rows:,} linhas)")
                else:
                    print(f" ✗ HTTP {response.status_code}")
                    
            except Exception as e:
                print(f" ✗ Erro: {str(e)}")
        
        if times:
            return {
                'method': name,
                'endpoint': endpoint,
                'runs': len(times),
                'avg_time': statistics.mean(times),
                'min_time': min(times),
                'max_time': max(times),
                'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
                'rows': row_counts[0] if row_counts else 0,
                'times': times
            }
        return None
    
    def compare_all(self):
        """Compara todos os métodos"""
        print("🚀 Comparação de Performance - Metabase Customizações")
        print("=" * 60)
        
        methods = [
            ("Native Performance", "/api/query/native"),
            ("Direct SQL", "/api/query/direct"),
            ("Metabase API", "/api/query"),
            ("Streaming SSE", "/api/query/stream")
        ]
        
        for name, endpoint in methods:
            result = self.test_method(name, endpoint)
            if result:
                self.results.append(result)
        
        self.show_results()
    
    def show_results(self):
        """Mostra resultados formatados"""
        if not self.results:
            print("\n❌ Nenhum resultado disponível")
            return
        
        # Ordena por tempo médio
        self.results.sort(key=lambda x: x['avg_time'])
        
        # Prepara tabela
        headers = ['Método', 'Linhas', 'Tempo Médio', 'Min', 'Max', 'Desvio', 'vs Melhor']
        rows = []
        
        best_time = self.results[0]['avg_time']
        
        for r in self.results:
            diff_percent = ((r['avg_time'] / best_time - 1) * 100) if best_time > 0 else 0
            
            rows.append([
                r['method'],
                f"{r['rows']:,}",
                f"{r['avg_time']:.2f}s",
                f"{r['min_time']:.2f}s",
                f"{r['max_time']:.2f}s",
                f"{r['std_dev']:.3f}s",
                f"+{diff_percent:.1f}%" if diff_percent > 0 else "🏆 Melhor"
            ])
        
        print("\n📊 RESULTADOS:")
        print(tabulate(rows, headers=headers, tablefmt='grid'))
        
        # Análise
        print("\n📈 ANÁLISE:")
        
        # Encontra native performance
        native = next((r for r in self.results if 'Native' in r['method']), None)
        direct = next((r for r in self.results if 'Direct' in r['method']), None)
        
        if native and direct:
            improvement = ((direct['avg_time'] - native['avg_time']) / direct['avg_time'] * 100)
            speed_factor = direct['avg_time'] / native['avg_time']
            
            print(f"\n✨ Native Performance é {speed_factor:.1f}x mais rápido que Direct SQL!")
            print(f"   Melhoria de {improvement:.1f}% no tempo de resposta")
            print(f"   Economia de {direct['avg_time'] - native['avg_time']:.2f} segundos por consulta")
            
            if native['rows'] > 0:
                native_speed = native['rows'] / native['avg_time']
                direct_speed = direct['rows'] / direct['avg_time']
                print(f"\n🚀 Velocidade de processamento:")
                print(f"   Native: {native_speed:,.0f} linhas/segundo")
                print(f"   Direct: {direct_speed:,.0f} linhas/segundo")
        
        # Gráfico ASCII
        self.plot_results()
    
    def plot_results(self):
        """Plota gráfico ASCII dos resultados"""
        print("\n📊 GRÁFICO DE BARRAS:")
        
        if not self.results:
            return
        
        max_time = max(r['avg_time'] for r in self.results)
        
        for r in self.results:
            bar_length = int((r['avg_time'] / max_time) * 50)
            bar = '█' * bar_length
            print(f"{r['method']:20s} |{bar} {r['avg_time']:.2f}s")
    
    def save_results(self):
        """Salva resultados em arquivo"""
        filename = f"performance_comparison_{time.strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': time.time(),
                'results': self.results,
                'summary': {
                    'best_method': self.results[0]['method'] if self.results else None,
                    'best_time': self.results[0]['avg_time'] if self.results else None
                }
            }, f, indent=2)
        
        print(f"\n💾 Resultados salvos em: {filename}")

def main():
    print("🎯 Teste de Performance - Metabase Customizações")
    print("Este teste compara a performance dos diferentes métodos")
    print("de carregamento de dados disponíveis.\n")
    
    comparator = PerformanceComparator()
    
    # Limpa cache antes de começar
    try:
        import redis
        r = redis.Redis()
        r.flushall()
        print("🗑️  Cache Redis limpo\n")
    except:
        pass
    
    comparator.compare_all()
    comparator.save_results()
    
    print("\n✅ Teste concluído!")

if __name__ == "__main__":
    # Instala tabulate se necessário
    try:
        import tabulate
    except ImportError:
        import subprocess
        print("📦 Instalando tabulate...")
        subprocess.check_call(["pip", "install", "tabulate"])
        import tabulate
    
    main()
