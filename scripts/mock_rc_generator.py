#!/usr/bin/env python3
"""
模拟RC生成器，用于测试整个流程
"""
import json
import re
from typing import Dict, List, Any, Optional

class MockRCGenerator:
    """模拟的Recent Changes生成器"""
    
    def __init__(self):
        # 预定义的模拟RC数据
        self.mock_responses = {
            "classloader": {
                "hunks": [
                    {
                        "path": "ClassLoaderUtils.java",
                        "type": "same_file",
                        "overlap": True,
                        "nearby": False,
                        "mini_diff": "@@ -10,6 +10,7 @@ public class ClassLoaderUtils {\n     private ClassLoaderUtils() {\n     }\n \n+    // TODO: Add application class loader support\n     @SuppressWarnings({\"unchecked\"})\n     public static URL[] getURLs(ClassLoader classLoader) {",
                        "after": [
                            "    private ClassLoaderUtils() {",
                            "    }",
                            "",
                            "    // TODO: Add application class loader support",
                            "    @SuppressWarnings({\"unchecked\"})",
                            "    public static URL[] getURLs(ClassLoader classLoader) {"
                        ]
                    },
                    {
                        "path": "ClassLoaderUtils.java", 
                        "type": "same_file",
                        "overlap": False,
                        "nearby": True,
                        "mini_diff": "@@ -25,7 +26,8 @@ public static URL[] getURLs(ClassLoader classLoader) {\n         } catch (Exception e) {\n-            throw new DevsporeCicException(e);\n+            log.warn(\"Failed to get URLs from classloader: {}\", e.getMessage());\n+            throw new DevsporeCicException(e);",
                        "after": [
                            "        } catch (Exception e) {",
                            "            log.warn(\"Failed to get URLs from classloader: {}\", e.getMessage());",
                            "            throw new DevsporeCicException(e);",
                            "        }"
                        ]
                    }
                ],
                "notes": "为ClassLoader工具类添加日志记录，提升调试能力"
            },
            "redis": {
                "hunks": [
                    {
                        "path": "RedisConnectionFactory.java",
                        "type": "same_file", 
                        "overlap": True,
                        "nearby": False,
                        "mini_diff": "@@ -15,6 +15,7 @@ public class RedisConnectionFactory {\n     private static final Logger log = LoggerFactory.getLogger(RedisConnectionFactory.class);\n \n+    // Redis connection configuration constants\n     private final LettuceConnectionFactory lettuceConnectionFactory;",
                        "after": [
                            "    private static final Logger log = LoggerFactory.getLogger(RedisConnectionFactory.class);",
                            "",
                            "    // Redis connection configuration constants", 
                            "    private final LettuceConnectionFactory lettuceConnectionFactory;"
                        ]
                    },
                    {
                        "path": "RedisConnectionFactory.java",
                        "type": "same_file",
                        "overlap": False,
                        "nearby": True,
                        "mini_diff": "@@ -45,6 +46,7 @@ private LettuceConnectionFactory createLettuceConnectionFactory(final RedisConf\n         if (RedisModeEnum.CLUSTER.getName().equals(redisConfigProperties.getMode())) {\n             return new LettuceConnectionFactory(redisClusterConfiguration(redisConfigProperties), lettuceClientConfiguration);\n         }\n+        // Default to standalone mode\n         return new LettuceConnectionFactory(redisStandaloneConfiguration(redisConfigProperties), lettuceClientConfiguration);",
                        "after": [
                            "        if (RedisModeEnum.CLUSTER.getName().equals(redisConfigProperties.getMode())) {",
                            "            return new LettuceConnectionFactory(redisClusterConfiguration(redisConfigProperties), lettuceClientConfiguration);",
                            "        }",
                            "        // Default to standalone mode",
                            "        return new LettuceConnectionFactory(redisStandaloneConfiguration(redisConfigProperties), lettuceClientConfiguration);"
                        ]
                    }
                ],
                "notes": "增强Redis连接工厂的配置注释和日志"
            },
            "jwt": {
                "hunks": [
                    {
                        "path": "JwtUtils.java",
                        "type": "same_file",
                        "overlap": True,
                        "nearby": False,
                        "mini_diff": "@@ -20,6 +20,7 @@ public class JwtUtils {\n     private static final Logger LOG = LoggerFactory.getLogger(JwtUtils.class);\n \n+    // JWT token generation constants\n     private static final Long TOKEN_EXPIRE_SECONDS = 24 * 60 * 60L;",
                        "after": [
                            "    private static final Logger LOG = LoggerFactory.getLogger(JwtUtils.class);",
                            "",
                            "    // JWT token generation constants",
                            "    private static final Long TOKEN_EXPIRE_SECONDS = 24 * 60 * 60L;"
                        ]
                    }
                ],
                "notes": "为JWT工具类添加常量说明注释"
            },
            "mybatis_interceptor": {
                "hunks": [
                    {
                        "path": "PostgreSQLQueryInterceptor.java",
                        "type": "same_file",
                        "overlap": True,
                        "nearby": False,
                        "mini_diff": "@@ -35,6 +35,7 @@ public class PostgreSQLQueryInterceptor implements Interceptor {\n \n     @Override\n     public Object intercept(final Invocation invocation) throws Throwable {\n+        // Extract query parameters for PostgreSQL optimization\n         Object[] args = invocation.getArgs();",
                        "after": [
                            "    @Override",
                            "    public Object intercept(final Invocation invocation) throws Throwable {",
                            "        // Extract query parameters for PostgreSQL optimization",
                            "        Object[] args = invocation.getArgs();"
                        ]
                    }
                ],
                "notes": "为MyBatis拦截器添加PostgreSQL优化说明"
            },
            "async_service": {
                "hunks": [
                    {
                        "path": "ApacheDubboProxyService.java",
                        "type": "same_file",
                        "overlap": False,
                        "nearby": True,
                        "mini_diff": "@@ -95,6 +95,7 @@ private CompletableFuture<Object> invokeAsync(final GenericService genericServi\n     @SuppressWarnings(\"unchecked\")\n     private CompletableFuture<Object> invokeAsync(final GenericService genericService, final String method, final String[] parameterTypes, final Object[] args) throws GenericException {\n+        // Async invocation for better performance\n         //Compatible with asynchronous calls of lower Dubbo versions",
                        "after": [
                            "    @SuppressWarnings(\"unchecked\")",
                            "    private CompletableFuture<Object> invokeAsync(final GenericService genericService, final String method, final String[] parameterTypes, final Object[] args) throws GenericException {",
                            "        // Async invocation for better performance", 
                            "        //Compatible with asynchronous calls of lower Dubbo versions"
                        ]
                    }
                ],
                "notes": "为异步服务调用添加性能优化说明"
            },
            "type_handler": {
                "hunks": [
                    {
                        "path": "PostgreSQLBooleanHandler.java",
                        "type": "same_file",
                        "overlap": True,
                        "nearby": False,
                        "mini_diff": "@@ -25,6 +25,7 @@ public class PostgreSQLBooleanHandler extends BaseTypeHandler<Boolean> {\n \n     @Override\n     public void setNonNullParameter(final PreparedStatement preparedStatement, final int columnIndex,\n+                                    // Convert Boolean to int for PostgreSQL compatibility\n                                     final Boolean columnValue, final JdbcType jdbcType) throws SQLException {",
                        "after": [
                            "    @Override",
                            "    public void setNonNullParameter(final PreparedStatement preparedStatement, final int columnIndex,",
                            "                                    // Convert Boolean to int for PostgreSQL compatibility",
                            "                                    final Boolean columnValue, final JdbcType jdbcType) throws SQLException {"
                        ]
                    }
                ],
                "notes": "为类型处理器添加PostgreSQL兼容性说明"
            }
        }
    
    def extract_code_context(self, prompt: str) -> Dict[str, str]:
        """从prompt中提取代码上下文"""
        context = {}
        
        # 提取上下文代码
        above_match = re.search(r'The context above is:\s*```java\s*(.*?)\s*```', prompt, re.DOTALL)
        if above_match:
            context['above'] = above_match.group(1).strip()
        
        below_match = re.search(r'The context below is:\s*```java\s*(.*?)\s*```', prompt, re.DOTALL)
        if below_match:
            context['below'] = below_match.group(1).strip()
        
        # 提取要实现的功能
        feature_match = re.search(r'The new feature is\s+(.*?)\.', prompt)
        if feature_match:
            context['feature'] = feature_match.group(1).strip()
        
        # 提取要修改的代码片段
        snippet_match = re.search(r'And here is the code snippet you are asked to modify:\s*```java\s*(.*?)\s*```', prompt, re.DOTALL)
        if snippet_match:
            context['target_snippet'] = snippet_match.group(1).strip()
        
        return context
    
    def determine_feature_type(self, context: Dict[str, str]) -> str:
        """根据上下文确定功能类型"""
        feature = context.get('feature', '').lower()
        code = (context.get('above', '') + context.get('below', '')).lower()
        
        if 'classloader' in feature or 'classloader' in code:
            return 'classloader'
        elif 'redis' in feature or 'redis' in code:
            return 'redis'
        elif 'jwt' in feature or 'jwt' in code:
            return 'jwt'
        elif 'mybatis' in feature or 'interceptor' in feature or 'mybatis' in code:
            return 'mybatis_interceptor'
        elif 'async' in feature or 'completablefuture' in code:
            return 'async_service'
        elif 'typehandler' in feature or 'typehandler' in code:
            return 'type_handler'
        else:
            return 'classloader'  # 默认类型
    
    def generate_rc_for_benchmark(self, benchmark_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """为单条benchmark生成RC"""
        prompt = benchmark_data.get('prompt', '')
        
        # 提取代码上下文
        context = self.extract_code_context(prompt)
        if not context:
            return None
        
        # 确定功能类型
        feature_type = self.determine_feature_type(context)
        
        # 获取对应的模拟响应
        mock_response = self.mock_responses.get(feature_type, self.mock_responses['classloader'])
        
        return mock_response

def main():
    """测试模拟生成器"""
    generator = MockRCGenerator()
    
    # 测试单条数据
    benchmark_file = "benchmark/nl2code_java_F10L.jsonl"
    with open(benchmark_file, 'r', encoding='utf-8') as f:
        first_line = f.readline()
        first_entry = json.loads(first_line.strip())
    
    print("=== 测试模拟RC生成 ===")
    print(f"处理benchmark: {first_entry.get('id', 'Unknown')}")
    
    rc_context = generator.generate_rc_for_benchmark(first_entry)
    if rc_context:
        print("生成成功!")
        print(f"Hunks数量: {len(rc_context['hunks'])}")
        print(f"Notes: {rc_context['notes']}")
        
        # 保存测试结果
        with open("mock_rc_output.json", 'w', encoding='utf-8') as f:
            json.dump(rc_context, f, indent=2, ensure_ascii=False)
        print("测试结果已保存到 mock_rc_output.json")
    else:
        print("生成失败!")

if __name__ == "__main__":
    main()
