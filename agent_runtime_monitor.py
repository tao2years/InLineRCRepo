#!/usr/bin/env python3
"""
Agent运行时监控器 - 实时捕获Agent执行状态和性能指标
专门用于深度调试Agent的内部机制和优化性能

功能特性:
1. 实时性能监控 (CPU, 内存, IO)
2. 方法调用链追踪
3. 异常和错误捕获
4. 资源使用分析
5. 执行时序分析
"""

import psutil
import threading
import time
import json
import traceback
import functools
import inspect
from datetime import datetime
from typing import Dict, List, Any, Callable
from collections import defaultdict, deque
import sys
import gc

class AgentRuntimeMonitor:
    """Agent运行时监控器"""
    
    def __init__(self, monitor_interval: float = 0.1):
        self.monitor_interval = monitor_interval
        self.is_monitoring = False
        self.monitor_thread = None
        
        # 性能数据存储
        self.performance_data = deque(maxlen=1000)  # 最近1000个数据点
        self.call_stack_data = []
        self.exception_data = []
        self.resource_usage = defaultdict(list)
        
        # 方法调用统计
        self.method_stats = defaultdict(lambda: {
            'call_count': 0,
            'total_time': 0,
            'avg_time': 0,
            'max_time': 0,
            'min_time': float('inf'),
            'errors': 0
        })
        
        # 当前执行状态
        self.current_context = {
            'active_methods': [],
            'call_depth': 0,
            'start_time': None
        }
        
        # BREAKPOINT: 监控器初始化完成 - 观察初始状态
        print(f"🔍 AgentRuntimeMonitor initialized with {monitor_interval}s interval")
    
    def start_monitoring(self):
        """开始监控"""
        if self.is_monitoring:
            return
        
        # BREAKPOINT: 监控启动 - 观察监控线程创建
        self.is_monitoring = True
        self.current_context['start_time'] = datetime.now()
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        print("📊 Runtime monitoring started")
    
    def stop_monitoring(self):
        """停止监控"""
        # BREAKPOINT: 监控停止 - 观察资源清理
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        
        print("⏹️ Runtime monitoring stopped")
    
    def _monitor_loop(self):
        """监控主循环"""
        process = psutil.Process()
        
        while self.is_monitoring:
            try:
                # BREAKPOINT: 每次监控循环 - 观察性能数据采集
                timestamp = datetime.now()
                
                # 收集系统性能数据
                cpu_percent = process.cpu_percent()
                memory_info = process.memory_info()
                io_counters = process.io_counters() if hasattr(process, 'io_counters') else None
                
                # 收集Python运行时数据
                gc_stats = gc.get_stats()
                thread_count = threading.active_count()
                
                performance_snapshot = {
                    'timestamp': timestamp.isoformat(),
                    'cpu_percent': cpu_percent,
                    'memory_rss': memory_info.rss,
                    'memory_vms': memory_info.vms,
                    'thread_count': thread_count,
                    'gc_collections': sum(stat['collections'] for stat in gc_stats),
                    'call_depth': self.current_context['call_depth'],
                    'active_methods': len(self.current_context['active_methods'])
                }
                
                if io_counters:
                    performance_snapshot.update({
                        'io_read_bytes': io_counters.read_bytes,
                        'io_write_bytes': io_counters.write_bytes,
                        'io_read_count': io_counters.read_count,
                        'io_write_count': io_counters.write_count
                    })
                
                # BREAKPOINT: 性能数据收集完成 - 观察数据结构
                self.performance_data.append(performance_snapshot)
                
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                # BREAKPOINT: 监控异常 - 观察异常处理
                self._record_exception("monitor_loop", e)
                time.sleep(self.monitor_interval)
    
    def method_tracer(self, func: Callable) -> Callable:
        """方法追踪装饰器"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            method_name = f"{func.__module__}.{func.__qualname__}"
            start_time = time.time()
            
            # BREAKPOINT: 方法调用开始 - 观察调用栈变化
            self.current_context['call_depth'] += 1
            self.current_context['active_methods'].append({
                'method': method_name,
                'start_time': start_time,
                'args_count': len(args),
                'kwargs_count': len(kwargs)
            })
            
            try:
                # BREAKPOINT: 方法执行前 - 观察参数和上下文
                result = func(*args, **kwargs)
                
                # 记录成功调用
                execution_time = time.time() - start_time
                self._update_method_stats(method_name, execution_time, success=True)
                
                # BREAKPOINT: 方法执行成功 - 观察返回值和性能
                return result
                
            except Exception as e:
                # 记录异常调用
                execution_time = time.time() - start_time
                self._update_method_stats(method_name, execution_time, success=False)
                self._record_exception(method_name, e)
                
                # BREAKPOINT: 方法执行异常 - 观察异常信息
                raise
                
            finally:
                # BREAKPOINT: 方法调用结束 - 观察清理过程
                self.current_context['call_depth'] -= 1
                if self.current_context['active_methods']:
                    self.current_context['active_methods'].pop()
        
        return wrapper
    
    def _update_method_stats(self, method_name: str, execution_time: float, success: bool):
        """更新方法统计信息"""
        # BREAKPOINT: 统计更新 - 观察统计计算过程
        stats = self.method_stats[method_name]
        stats['call_count'] += 1
        stats['total_time'] += execution_time
        stats['avg_time'] = stats['total_time'] / stats['call_count']
        
        if execution_time > stats['max_time']:
            stats['max_time'] = execution_time
        if execution_time < stats['min_time']:
            stats['min_time'] = execution_time
            
        if not success:
            stats['errors'] += 1
    
    def _record_exception(self, context: str, exception: Exception):
        """记录异常信息"""
        # BREAKPOINT: 异常记录 - 观察异常数据结构
        exception_info = {
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'traceback': traceback.format_exc(),
            'call_depth': self.current_context['call_depth'],
            'active_methods': list(self.current_context['active_methods'])
        }
        
        self.exception_data.append(exception_info)
    
    def capture_memory_snapshot(self, label: str = ""):
        """捕获内存快照"""
        # BREAKPOINT: 内存快照 - 观察内存分析
        gc.collect()  # 强制垃圾回收
        
        memory_snapshot = {
            'timestamp': datetime.now().isoformat(),
            'label': label,
            'objects_count': len(gc.get_objects()),
            'memory_usage': psutil.Process().memory_info().rss,
            'gc_stats': gc.get_stats()
        }
        
        self.resource_usage['memory_snapshots'].append(memory_snapshot)
        return memory_snapshot
    
    def analyze_performance_trends(self) -> Dict[str, Any]:
        """分析性能趋势"""
        if not self.performance_data:
            return {}
        
        # BREAKPOINT: 性能分析开始 - 观察数据处理
        data_points = list(self.performance_data)
        
        # CPU趋势分析
        cpu_values = [point['cpu_percent'] for point in data_points]
        memory_values = [point['memory_rss'] for point in data_points]
        
        analysis = {
            'data_points_count': len(data_points),
            'time_range': {
                'start': data_points[0]['timestamp'],
                'end': data_points[-1]['timestamp']
            },
            'cpu_analysis': {
                'avg': sum(cpu_values) / len(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values),
                'trend': 'increasing' if cpu_values[-1] > cpu_values[0] else 'decreasing'
            },
            'memory_analysis': {
                'avg': sum(memory_values) / len(memory_values),
                'max': max(memory_values),
                'min': min(memory_values),
                'growth': memory_values[-1] - memory_values[0]
            }
        }
        
        # BREAKPOINT: 性能分析完成 - 观察分析结果
        return analysis
    
    def get_top_methods(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最耗时的方法"""
        # BREAKPOINT: 方法排序 - 观察性能排序逻辑
        sorted_methods = sorted(
            self.method_stats.items(),
            key=lambda x: x[1]['total_time'],
            reverse=True
        )
        
        return [
            {
                'method': method,
                'stats': stats
            }
            for method, stats in sorted_methods[:limit]
        ]
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """生成综合报告"""
        # BREAKPOINT: 报告生成 - 观察数据汇总
        report = {
            'session_info': {
                'start_time': self.current_context['start_time'].isoformat() if self.current_context['start_time'] else None,
                'end_time': datetime.now().isoformat(),
                'monitoring_interval': self.monitor_interval
            },
            'performance_summary': self.analyze_performance_trends(),
            'method_statistics': dict(self.method_stats),
            'top_methods': self.get_top_methods(),
            'exception_summary': {
                'total_exceptions': len(self.exception_data),
                'exception_types': list(set(exc['exception_type'] for exc in self.exception_data)),
                'recent_exceptions': self.exception_data[-5:] if self.exception_data else []
            },
            'resource_usage': dict(self.resource_usage),
            'current_state': {
                'call_depth': self.current_context['call_depth'],
                'active_methods': self.current_context['active_methods']
            }
        }
        
        # BREAKPOINT: 报告完成 - 观察最终报告结构
        return report
    
    def save_report(self, filename: str = None):
        """保存监控报告"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"agent_runtime_report_{timestamp}.json"
        
        # BREAKPOINT: 报告保存 - 观察文件写入
        report = self.generate_comprehensive_report()
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"📄 Runtime report saved to: {filename}")
            return filename
        except Exception as e:
            print(f"❌ Failed to save report: {e}")
            return None

# 全局监控器实例
_global_monitor = None

def get_monitor() -> AgentRuntimeMonitor:
    """获取全局监控器实例"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = AgentRuntimeMonitor()
    return _global_monitor

def monitor_method(func: Callable) -> Callable:
    """方法监控装饰器 - 便捷使用"""
    return get_monitor().method_tracer(func)

def start_global_monitoring():
    """启动全局监控"""
    get_monitor().start_monitoring()

def stop_global_monitoring():
    """停止全局监控"""
    get_monitor().stop_monitoring()

def save_monitoring_report():
    """保存监控报告"""
    return get_monitor().save_report()

# 示例使用
if __name__ == "__main__":
    # BREAKPOINT: 示例程序开始 - 观察监控器使用
    monitor = AgentRuntimeMonitor()
    monitor.start_monitoring()
    
    @monitor.method_tracer
    def example_heavy_computation():
        """示例重计算方法"""
        # BREAKPOINT: 重计算开始 - 观察性能影响
        result = sum(i * i for i in range(100000))
        time.sleep(0.1)  # 模拟IO等待
        return result
    
    @monitor.method_tracer
    def example_memory_operation():
        """示例内存操作"""
        # BREAKPOINT: 内存操作 - 观察内存分配
        large_list = list(range(50000))
        monitor.capture_memory_snapshot("after_large_allocation")
        return len(large_list)
    
    try:
        # 执行示例操作
        for i in range(5):
            # BREAKPOINT: 循环执行 - 观察累积效应
            result1 = example_heavy_computation()
            result2 = example_memory_operation()
            time.sleep(0.2)
        
        # 生成并保存报告
        report_file = monitor.save_report()
        print(f"✅ Monitoring completed, report saved to: {report_file}")
        
    finally:
        # BREAKPOINT: 清理阶段 - 观察资源释放
        monitor.stop_monitoring()
