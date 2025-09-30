#!/usr/bin/env python3
"""
Visualize ULID benchmark results using seaborn and matplotlib.
"""

import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List

# Set style
plt.style.use('default')
sns.set_palette("husl")

def load_results() -> Dict:
    """Load consolidated benchmark results."""
    results_file = Path("consolidated_results.json")
    
    if not results_file.exists():
        raise FileNotFoundError(
            "No results found. Run 'python docker-benchmark/run_benchmark.py' first."
        )
    
    with open(results_file, 'r') as f:
        return json.load(f)

def prepare_dataframe(results: Dict) -> pd.DataFrame:
    """Convert results to pandas DataFrame for visualization."""
    data = []
    
    for result in results['results']:
        if 'error' in result:
            continue
            
        library = result['library']
        
        # Extract performance metrics
        gen_ops = result.get('generation', {}).get('ops_per_sec', 0)
        parse_ops = result.get('parsing', {}).get('ops_per_sec', 0)
        
        # Extract memory metrics
        gen_mem = result.get('generation', {}).get('memory_overhead_mb', 0)
        parse_mem = result.get('parsing', {}).get('memory_overhead_mb', 0)
        
        # Add rows for each operation type
        data.extend([
            {
                'Library': library,
                'Operation': 'Generation',
                'Ops_per_sec': gen_ops,
                'Memory_MB': gen_mem,
                'Log_Ops_per_sec': np.log10(gen_ops) if gen_ops > 0 else 0
            },
            {
                'Library': library,
                'Operation': 'Parsing',
                'Ops_per_sec': parse_ops,
                'Memory_MB': parse_mem,
                'Log_Ops_per_sec': np.log10(parse_ops) if parse_ops > 0 else 0
            }
        ])
    
    return pd.DataFrame(data)

def create_performance_chart(df: pd.DataFrame, benchmark_info: Dict):
    """Create comprehensive performance visualization."""
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('ULID Libraries Performance Benchmark\n'
                f'Resource Limits: {benchmark_info["memory_limit"]} RAM, '
                f'{benchmark_info["cpu_limit"]} CPU cores', 
                fontsize=16, fontweight='bold')
    
    # 1. Operations per second (log scale for better visualization)
    ax1 = axes[0, 0]
    sns.barplot(data=df, x='Library', y='Ops_per_sec', hue='Operation', ax=ax1)
    ax1.set_yscale('log')
    ax1.set_title('Performance Comparison (Log Scale)', fontweight='bold')
    ax1.set_ylabel('Operations per Second (log scale)')
    ax1.tick_params(axis='x', rotation=45)
    ax1.legend(title='Operation Type')
    
    # Add value labels on bars
    for container in ax1.containers:
        ax1.bar_label(container, fmt='%.0f', fontsize=8)
    
    # 2. Generation performance only (linear scale)
    ax2 = axes[0, 1]
    gen_df = df[df['Operation'] == 'Generation']
    bars = sns.barplot(data=gen_df, x='Library', y='Ops_per_sec', ax=ax2, 
                      palette='viridis')
    ax2.set_title('ULID Generation Performance', fontweight='bold')
    ax2.set_ylabel('Operations per Second')
    ax2.tick_params(axis='x', rotation=45)
    
    # Add value labels
    for i, bar in enumerate(bars.patches):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{height:,.0f}', ha='center', va='bottom', fontsize=10)
    
    # 3. Memory usage comparison  
    ax3 = axes[1, 0]
    sns.boxplot(data=df, x='Library', y='Memory_MB', ax=ax3, palette='Set2')
    ax3.set_title('Memory Usage by Library', fontweight='bold')
    ax3.set_ylabel('Memory Overhead (MB)')
    ax3.tick_params(axis='x', rotation=45)
    
    # 4. Performance vs Memory scatter
    ax4 = axes[1, 1]
    
    # Create scatter plot for each operation type
    operations = df['Operation'].unique()
    colors = sns.color_palette('husl', len(operations))
    
    for i, op in enumerate(operations):
        op_df = df[df['Operation'] == op]
        ax4.scatter(op_df['Memory_MB'], op_df['Ops_per_sec'], 
                   label=op, alpha=0.7, s=100, color=colors[i])
        
        # Add library labels
        for _, row in op_df.iterrows():
            ax4.annotate(row['Library'], 
                        (row['Memory_MB'], row['Ops_per_sec']),
                        xytext=(5, 5), textcoords='offset points',
                        fontsize=8, alpha=0.8)
    
    ax4.set_yscale('log')
    ax4.set_title('Performance vs Memory Usage', fontweight='bold')
    ax4.set_xlabel('Memory Overhead (MB)')
    ax4.set_ylabel('Operations per Second (log scale)')
    ax4.legend(title='Operation Type')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save the chart
    output_file = 'ulid_benchmark_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 Chart saved as: {output_file}")
    
    return fig

def create_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """Create summary table of results."""
    
    # Pivot to get operations as columns
    summary = df.pivot_table(
        index='Library', 
        columns='Operation', 
        values='Ops_per_sec', 
        aggfunc='first'
    ).fillna(0)
    
    # Calculate relative performance (compared to best in each category)
    for col in summary.columns:
        max_val = summary[col].max()
        if max_val > 0:
            summary[f'{col}_Relative'] = (summary[col] / max_val * 100).round(1)
    
    # Add overall score (average of relative performance)
    relative_cols = [col for col in summary.columns if '_Relative' in col]
    summary['Overall_Score'] = summary[relative_cols].mean(axis=1).round(1)
    
    return summary

def print_summary_table(summary: pd.DataFrame):
    """Print formatted summary table."""
    print("\n" + "="*60)
    print("DOCKER BENCHMARK SUMMARY (Operations per Second)")
    print("="*60)
    
    # Print absolute performance
    print(f"{'Library':<15} {'Generation':<12} {'Parsing':<12}")
    print("-" * 60)
    
    for library in summary.index:
        gen = summary.loc[library, 'Generation']
        parse = summary.loc[library, 'Parsing']
        
        print(f"{library:<15} {gen:>11,.0f} {parse:>11,.0f}")
    
    print("="*60)
    
    # Print relative performance
    print("\nRELATIVE PERFORMANCE (% of best performer)")
    print("-" * 60)
    print(f"{'Library':<15} {'Generation':<12} {'Parsing':<12} {'Overall':<10}")
    print("-" * 60)
    
    for library in summary.index:
        gen_rel = summary.loc[library, 'Generation_Relative']
        parse_rel = summary.loc[library, 'Parsing_Relative']
        overall = summary.loc[library, 'Overall_Score']
        
        print(f"{library:<15} {gen_rel:>10.1f}% {parse_rel:>10.1f}% {overall:>8.1f}%")
    
    print("="*60)

def main():
    """Main visualization function."""
    try:
        # Load results
        print("📊 Loading benchmark results...")
        data = load_results()
        
        benchmark_info = data['benchmark_info']
        
        # Prepare data
        df = prepare_dataframe(data)
        
        if df.empty:
            print("❌ No valid results found to visualize.")
            return 1
        
        print(f"📈 Processing results for {len(df['Library'].unique())} libraries...")
        
        # Create visualizations
        fig = create_performance_chart(df, benchmark_info)
        
        # Create and display summary
        summary = create_summary_table(df)
        print_summary_table(summary)
        
        # Save summary to CSV
        summary_file = 'benchmark_summary.csv'
        summary.to_csv(summary_file)
        print(f"\n📋 Summary saved to: {summary_file}")
        
        print("\n🎉 Visualization complete!")
        print("Check 'ulid_benchmark_comparison.png' for the charts.")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return 1
    except Exception as e:
        print(f"❌ Error creating visualization: {e}")
        return 1

if __name__ == "__main__":
    exit(main())