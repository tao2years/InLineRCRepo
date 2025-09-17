#!/usr/bin/env python3
"""
RC生成策略设计
"""
import json
import os
from typing import Dict, List, Any, Tuple

class RCGenerationStrategy:
    """Recent Changes生成策略类"""
    
    def __init__(self):
        # 将benchmark中的功能映射到shenyu项目中的相应文件
        self.benchmark_to_shenyu_mapping = {
            # ClassLoader相关功能 -> shenyu的插件类加载器
            "devspore-cic_30036124#4": {
                "shenyu_file": "shenyu/shenyu-web/src/main/java/org/apache/shenyu/web/loader/ShenyuPluginClassLoader.java",
                "feature_type": "classloader",
                "description": "使用系统的Application ClassLoader来加载一个指定的类"
            },
            "devspore-cic_30036124#21": {
                "shenyu_file": "shenyu/shenyu-web/src/main/java/org/apache/shenyu/web/loader/ShenyuPluginLoader.java",
                "feature_type": "classloader",
                "description": "判断给定类是否为Bootstrap ClassLoader"
            },
            "devspore-cic_30036124#22": {
                "shenyu_file": "shenyu/shenyu-web/src/main/java/org/apache/shenyu/web/loader/ShenyuPluginClassLoaderHolder.java",
                "feature_type": "classloader",
                "description": "获取Extension ClassLoader加载路径"
            },
            
            # Redis连接工厂相关 -> shenyu的Redis基础设施
            "DevUC-common_x00636091#6": {
                "shenyu_file": "shenyu/shenyu-infra/shenyu-infra-redis/src/main/java/org/apache/shenyu/infra/redis/RedisConnectionFactory.java",
                "feature_type": "redis",
                "description": "根据JinCacheRedisConfiguration创建RedisClusterConfiguration，并生成JedisConnectionFactory"
            },
            "APITestDesign-l00617778#10": {
                "shenyu_file": "shenyu/shenyu-plugin/shenyu-plugin-cache/shenyu-plugin-cache-redis/src/main/java/org/apache/shenyu/plugin/cache/redis/RedisCache.java",
                "feature_type": "redis",
                "description": "使用RedisTemplate实现taskid前缀的hash查询"
            },
            
            # JWT相关 -> shenyu的JWT工具和插件
            "nacos_f00563108#25": {
                "shenyu_file": "shenyu/shenyu-admin/src/main/java/org/apache/shenyu/admin/utils/JwtUtils.java",
                "feature_type": "jwt",
                "description": "根据JWT token的结构，生成JWT token"
            },
            
            # MyBatis拦截器相关 -> shenyu的数据库拦截器
            "octopusscheduler_f00563108#27": {
                "shenyu_file": "shenyu/shenyu-admin/src/main/java/org/apache/shenyu/admin/mybatis/pg/interceptor/PostgreSQLQueryInterceptor.java",
                "feature_type": "mybatis_interceptor",
                "description": "自定义一个mybatis的拦截器，拦截sql后增加自定义行为并执行"
            },
            
            # 异步服务相关 -> shenyu的异步代理服务
            "SnapEngineService_h00636345#28": {
                "shenyu_file": "shenyu/shenyu-plugin/shenyu-plugin-proxy/shenyu-plugin-rpc/shenyu-plugin-dubbo/shenyu-plugin-apache-dubbo/src/main/java/org/apache/shenyu/plugin/apache/dubbo/proxy/ApacheDubboProxyService.java",
                "feature_type": "async_service",
                "description": "异步记录风控拦截记录"
            },
            
            # TypeHandler相关 -> shenyu的自定义类型处理器
            "octopusscheduler_f00563108#31": {
                "shenyu_file": "shenyu/shenyu-admin/src/main/java/org/apache/shenyu/admin/mybatis/pg/handler/PostgreSQLBooleanHandler.java",
                "feature_type": "type_handler",
                "description": "自定义mybatis json typeHandler"
            },
            "octopusscheduler_f00563108#32": {
                "shenyu_file": "shenyu/shenyu-admin/src/main/java/org/apache/shenyu/admin/mybatis/og/handler/OpenGaussSQLBooleanHandler.java",
                "feature_type": "type_handler",
                "description": "自定义mybatis List typeHandler"
            }
        }
    
    def get_shenyu_mapping(self, benchmark_id: str) -> Dict[str, Any]:
        """获取benchmark ID对应的shenyu文件映射"""
        return self.benchmark_to_shenyu_mapping.get(benchmark_id, {})
    
    def get_neighbor_files(self, shenyu_file: str) -> List[str]:
        """获取邻居文件列表"""
        if not shenyu_file:
            return []
        
        # 获取同目录下的其他Java文件
        dir_path = os.path.dirname(shenyu_file)
        neighbors = []
        
        # 根据不同的目录类型，推荐相关的邻居文件
        if "loader" in dir_path:
            neighbors = [
                "shenyu/shenyu-web/src/main/java/org/apache/shenyu/web/loader/ShenyuPluginPathBuilder.java",
                "shenyu/shenyu-web/src/main/java/org/apache/shenyu/web/loader/PluginJarParser.java"
            ]
        elif "redis" in dir_path:
            neighbors = [
                "shenyu/shenyu-infra/shenyu-infra-redis/src/main/java/org/apache/shenyu/infra/redis/RedisConfigProperties.java",
                "shenyu/shenyu-plugin/shenyu-plugin-cache/shenyu-plugin-cache-redis/src/main/java/org/apache/shenyu/plugin/cache/redis/RedisCacheBuilder.java"
            ]
        elif "jwt" in dir_path or "JwtUtils" in shenyu_file:
            neighbors = [
                "shenyu/shenyu-plugin/shenyu-plugin-security/shenyu-plugin-jwt/src/main/java/org/apache/shenyu/plugin/jwt/JwtPlugin.java"
            ]
        elif "mybatis" in dir_path and "interceptor" in dir_path:
            neighbors = [
                "shenyu/shenyu-admin/src/main/java/org/apache/shenyu/admin/mybatis/og/interceptor/OpenGaussSQLQueryInterceptor.java"
            ]
        elif "mybatis" in dir_path and "handler" in dir_path:
            neighbors = [
                "shenyu/shenyu-admin/src/main/java/org/apache/shenyu/admin/mybatis/pg/handler/PostgreSQLBooleanHandler.java",
                "shenyu/shenyu-admin/src/main/java/org/apache/shenyu/admin/mybatis/og/handler/OpenGaussSQLBooleanHandler.java"
            ]
        elif "proxy" in dir_path:
            neighbors = [
                "shenyu/shenyu-plugin/shenyu-plugin-proxy/shenyu-plugin-rpc/shenyu-plugin-dubbo/shenyu-plugin-alibaba-dubbo/src/main/java/org/apache/shenyu/plugin/alibaba/dubbo/proxy/AlibabaDubboProxyService.java"
            ]
        
        # 过滤掉主文件本身
        return [f for f in neighbors if f != shenyu_file]
    
    def generate_rc_context_structure(self, benchmark_id: str, benchmark_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成RC上下文的基本结构"""
        mapping = self.get_shenyu_mapping(benchmark_id)
        
        if not mapping:
            # 如果没有映射，使用默认的shenyu文件
            mapping = {
                "shenyu_file": "shenyu/shenyu-common/src/main/java/org/apache/shenyu/common/utils/StringUtils.java",
                "feature_type": "utility",
                "description": benchmark_data.get('extra_content', {}).get('query', 'Unknown feature')
            }
        
        shenyu_file = mapping["shenyu_file"]
        neighbors = self.get_neighbor_files(shenyu_file)
        
        return {
            "benchmark_id": benchmark_id,
            "original_feature": benchmark_data.get('extra_content', {}).get('query', ''),
            "shenyu_main_file": shenyu_file,
            "shenyu_neighbor_files": neighbors,
            "feature_type": mapping.get("feature_type", "unknown"),
            "rc_context": {
                "hunks": [],  # 将由LLM生成
                "notes": ""   # 将由LLM生成
            }
        }

def main():
    """主函数，展示策略设计"""
    strategy = RCGenerationStrategy()
    
    print("=== RC生成策略设计 ===\n")
    
    # 读取benchmark数据
    benchmark_file = "benchmark/nl2code_java_F10L.jsonl"
    with open(benchmark_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            entry = json.loads(line.strip())
            benchmark_id = entry.get('id', '')
            
            print(f"第{line_num}条数据: {benchmark_id}")
            
            # 生成RC上下文结构
            rc_structure = strategy.generate_rc_context_structure(benchmark_id, entry)
            
            print(f"  原始功能: {rc_structure['original_feature']}")
            print(f"  映射到shenyu文件: {rc_structure['shenyu_main_file']}")
            print(f"  邻居文件数量: {len(rc_structure['shenyu_neighbor_files'])}")
            if rc_structure['shenyu_neighbor_files']:
                print(f"  邻居文件: {rc_structure['shenyu_neighbor_files'][0]}")
            print(f"  功能类型: {rc_structure['feature_type']}")
            print()

if __name__ == "__main__":
    main()
