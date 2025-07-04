"""
Serviço de cache usando Redis
"""

import json
import gzip
import time
from typing import Dict, Optional
from config.settings import REDIS_CONFIG, CACHE_CONFIG

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️ Redis não instalado, cache desabilitado")

class CacheService:
    """Gerencia cache com Redis"""
    
    def __init__(self):
        self.enabled = CACHE_CONFIG['enabled'] and REDIS_CONFIG['enabled'] and REDIS_AVAILABLE
        self.ttl = CACHE_CONFIG['ttl']
        self.redis_client = None
        
        if self.enabled:
            try:
                self.redis_client = redis.Redis(
                    host=REDIS_CONFIG['host'],
                    port=REDIS_CONFIG['port'],
                    decode_responses=False  # Usamos bytes para performance
                )
                # Testa conexão
                self.redis_client.ping()
                print("✅ Cache Redis conectado")
            except Exception as e:
                print(f"⚠️ Erro ao conectar Redis: {e}")
                self.enabled = False
    
    def get(self, key: str) -> Optional[Dict]:
        """Obtém valor do cache"""
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            data = self.redis_client.get(f"metabase:query:{key}")
            if data:
                # Descomprime e deserializa
                decompressed = gzip.decompress(data)
                return json.loads(decompressed.decode('utf-8'))
        except Exception as e:
            print(f"⚠️ Erro ao ler cache: {e}")
        
        return None
    
    def set(self, key: str, value: Dict):
        """Salva valor no cache"""
        if not self.enabled or not self.redis_client:
            return
        
        try:
            # Serializa e comprime
            json_data = json.dumps(value, separators=(',', ':'))
            compressed = gzip.compress(json_data.encode('utf-8'))
            
            # Salva com TTL
            self.redis_client.setex(
                f"metabase:query:{key}",
                self.ttl,
                compressed
            )
            
            print(f"💾 Cache salvo: {len(json_data)} → {len(compressed)} bytes "
                  f"({100 - len(compressed)/len(json_data)*100:.1f}% compressão)")
            
        except Exception as e:
            print(f"⚠️ Erro ao salvar cache: {e}")
    
    def delete(self, key: str):
        """Remove valor do cache"""
        if not self.enabled or not self.redis_client:
            return
        
        try:
            self.redis_client.delete(f"metabase:query:{key}")
        except Exception as e:
            print(f"⚠️ Erro ao deletar cache: {e}")
    
    def clear_all(self):
        """Limpa todo o cache"""
        if not self.enabled or not self.redis_client:
            return
        
        try:
            # Remove apenas chaves do metabase
            pattern = "metabase:query:*"
            for key in self.redis_client.scan_iter(match=pattern):
                self.redis_client.delete(key)
            print("🗑️ Cache Redis limpo")
        except Exception as e:
            print(f"⚠️ Erro ao limpar cache: {e}")
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do cache"""
        if not self.enabled or not self.redis_client:
            return {'enabled': False}
        
        try:
            info = self.redis_client.info()
            pattern = "metabase:query:*"
            keys_count = len(list(self.redis_client.scan_iter(match=pattern)))
            
            return {
                'enabled': True,
                'keys_count': keys_count,
                'memory_used': info.get('used_memory_human', 'N/A'),
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0),
                'uptime': info.get('uptime_in_seconds', 0)
            }
        except Exception as e:
            return {'enabled': True, 'error': str(e)}
