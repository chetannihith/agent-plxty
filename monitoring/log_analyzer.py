"""
Log Analysis Utility for Resume Optimizer

Analyzes JSONL logs to provide insights and metrics.
"""
import json
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict
import statistics


class LogAnalyzer:
    """Analyzes workflow execution logs"""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.events = []
        self._load_logs()
    
    def _load_logs(self):
        """Load events from JSONL file"""
        if not self.log_file.exists():
            print(f"Log file not found: {self.log_file}")
            return
        
        with open(self.log_file, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        self.events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    
    def get_execution_timeline(self) -> List[Dict[str, Any]]:
        """Get chronological timeline of events"""
        return sorted(self.events, key=lambda x: x['timestamp'])
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get statistics per agent"""
        agent_stats = defaultdict(lambda: {
            'calls': 0,
            'execution_times': [],
            'llm_calls': 0,
            'tool_calls': 0
        })
        
        for event in self.events:
            details = event.get('details', {})
            agent_name = details.get('agent_name')
            
            if not agent_name:
                continue
            
            if event['event_type'] == 'agent_start':
                agent_stats[agent_name]['calls'] += 1
            elif event['event_type'] == 'agent_complete':
                exec_time = details.get('execution_time_seconds', 0)
                agent_stats[agent_name]['execution_times'].append(exec_time)
            elif event['event_type'] == 'llm_call':
                agent_stats[agent_name]['llm_calls'] += 1
            elif event['event_type'] == 'tool_call':
                agent_stats[agent_name]['tool_calls'] += 1
        
        # Calculate averages
        for agent_name, stats in agent_stats.items():
            times = stats['execution_times']
            if times:
                stats['avg_execution_time'] = statistics.mean(times)
                stats['max_execution_time'] = max(times)
                stats['min_execution_time'] = min(times)
        
        return dict(agent_stats)
    
    def get_summary_report(self) -> str:
        """Generate a human-readable summary report"""
        stats = self.get_agent_statistics()
        
        report = []
        report.append("=" * 80)
        report.append("WORKFLOW EXECUTION ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"\nTotal Events Logged: {len(self.events)}")
        report.append(f"Total Agents: {len(stats)}")
        report.append("\n" + "-" * 80)
        report.append("AGENT STATISTICS")
        report.append("-" * 80)
        
        for agent_name, agent_stats in sorted(stats.items()):
            report.append(f"\n{agent_name}:")
            report.append(f"  Calls: {agent_stats['calls']}")
            report.append(f"  LLM Calls: {agent_stats['llm_calls']}")
            report.append(f"  Tool Calls: {agent_stats['tool_calls']}")
            if agent_stats['execution_times']:
                report.append(f"  Avg Execution Time: {agent_stats['avg_execution_time']:.2f}s")
                report.append(f"  Max Execution Time: {agent_stats['max_execution_time']:.2f}s")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)
    
    def save_report(self, output_file: Path):
        """Save analysis report to file"""
        report = self.get_summary_report()
        with open(output_file, 'w') as f:
            f.write(report)
        print(f"Report saved to: {output_file}")


def analyze_logs(log_file: str = "workflow_execution.jsonl"):
    """Convenience function to analyze logs"""
    log_path = Path("./logs") / log_file
    analyzer = LogAnalyzer(log_path)
    
    if analyzer.events:
        print(analyzer.get_summary_report())
        
        # Save to file
        report_path = Path("./logs") / "execution_report.txt"
        analyzer.save_report(report_path)
    else:
        print(f"No events found in {log_path}")


if __name__ == "__main__":
    analyze_logs()
