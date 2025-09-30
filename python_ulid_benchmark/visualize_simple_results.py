#!/usr/bin/env python3
"""
Simple visualization for quick benchmark results.
Creates clean performance charts and summary report without symbols.
"""

import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

# Set style for professional charts
plt.style.use("default")
sns.set_palette("husl")

def load_results() -> List[Dict[str, Any]]:
    """Load all JSON result files."""
    results = []
    
    json_files = [
        "ulid-python.json",
        "python-ulid.json", 
        "py-ulid.json",
        "ulid-py.json"
    ]
    
    for file in json_files:
        if Path(file).exists():
            with open(file, "r") as f:
                data = json.load(f)
                results.append(data)
                print(f"Loaded {file}")
        else:
            print(f"File not found: {file}")
    
    return results

def create_performance_dataframe(results: List[Dict]) -> pd.DataFrame:
    """Create DataFrame with performance metrics."""
    data = []
    
    for result in results:
        library = result["library"]
        
        # Generation performance
        gen_data = result.get("generation", {})
        if gen_data.get("success", False):
            gen_ops = gen_data.get("ops_per_sec", 0)
            gen_memory = gen_data.get("memory_overhead_mb", 0)
        else:
            gen_ops = 0
            gen_memory = 0
        
        # Parsing performance  
        parse_data = result.get("parsing", {})
        if parse_data.get("success", False):
            parse_ops = parse_data.get("ops_per_sec", 0)
            parse_memory = parse_data.get("memory_overhead_mb", 0)
        else:
            parse_ops = 0
            parse_memory = 0
        
        data.append({
            "Library": library,
            "Generation_OPS": gen_ops,
            "Parsing_OPS": parse_ops,
            "Generation_Memory_MB": gen_memory,
            "Parsing_Memory_MB": parse_memory,
            "Python_Version": result.get("system_info", {}).get("python_version", "Unknown")
        })
    
    return pd.DataFrame(data)

def calculate_relative_performance(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate relative performance percentages."""
    df = df.copy()
    
    # Calculate relative performance (best = 100%)
    max_gen = df["Generation_OPS"].max()
    max_parse = df["Parsing_OPS"].max()
    
    df["Generation_Relative"] = (df["Generation_OPS"] / max_gen * 100) if max_gen > 0 else 0
    df["Parsing_Relative"] = (df["Parsing_OPS"] / max_parse * 100) if max_parse > 0 else 0
    
    # Overall score (average of both categories)
    df["Overall_Score"] = (df["Generation_Relative"] + df["Parsing_Relative"]) / 2
    
    return df

def create_visualizations(df: pd.DataFrame):
    """Create performance visualizations."""
    
    # Set up the figure with subplots
    fig = plt.figure(figsize=(16, 12))
    
    # 1. Performance Comparison (Bar Chart)
    ax1 = plt.subplot(2, 2, 1)
    x = range(len(df))
    width = 0.35
    
    gen_bars = ax1.bar([i - width/2 for i in x], df["Generation_OPS"] / 1e6, 
                       width, label="Generation", alpha=0.8)
    parse_bars = ax1.bar([i + width/2 for i in x], df["Parsing_OPS"] / 1e6, 
                        width, label="Parsing", alpha=0.8)
    
    ax1.set_xlabel("ULID Libraries")
    ax1.set_ylabel("Performance (Million ops/sec)")
    ax1.set_title("Performance Comparison", fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(df["Library"], rotation=45, ha="right")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar in gen_bars:
        height = bar.get_height()
        if height > 0:
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f"{height:.1f}M", ha="center", va="bottom", fontsize=9)
    
    for bar in parse_bars:
        height = bar.get_height()
        if height > 0:
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f"{height:.1f}M", ha="center", va="bottom", fontsize=9)
    
    # 2. Memory Usage Comparison
    ax2 = plt.subplot(2, 2, 2)
    gen_mem_bars = ax2.bar([i - width/2 for i in x], df["Generation_Memory_MB"], 
                          width, label="Generation", alpha=0.8)
    parse_mem_bars = ax2.bar([i + width/2 for i in x], df["Parsing_Memory_MB"], 
                           width, label="Parsing", alpha=0.8)
    
    ax2.set_xlabel("ULID Libraries")
    ax2.set_ylabel("Memory Overhead (MB)")
    ax2.set_title("Memory Usage Comparison", fontweight="bold")
    ax2.set_xticks(x)
    ax2.set_xticklabels(df["Library"], rotation=45, ha="right")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Add value labels
    for bar in gen_mem_bars:
        height = bar.get_height()
        if height > 0:
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                    f"{height:.1f}", ha="center", va="bottom", fontsize=9)
    
    for bar in parse_mem_bars:
        height = bar.get_height()
        if height > 0:
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                    f"{height:.1f}", ha="center", va="bottom", fontsize=9)
    
    # 3. Overall Performance Score
    ax3 = plt.subplot(2, 2, 3)
    rel_bars = ax3.bar(df["Library"], df["Overall_Score"], alpha=0.8, 
                       color=["#2E8B57" if score > 90 else "#FF6347" if score < 30 else "#4682B4" 
                              for score in df["Overall_Score"]])
    
    ax3.set_ylabel("Overall Score (%)")
    ax3.set_title("Overall Performance Score", fontweight="bold")
    plt.setp(ax3.get_xticklabels(), rotation=45, ha="right")
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0, 105)
    
    # Add value labels
    for bar in rel_bars:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 1,
                f"{height:.1f}%", ha="center", va="bottom", fontweight="bold")
    
    # 4. Log Scale Performance Comparison
    ax4 = plt.subplot(2, 2, 4)
    gen_log_bars = ax4.bar([i - width/2 for i in x], df["Generation_OPS"], 
                          width, label="Generation", alpha=0.8)
    parse_log_bars = ax4.bar([i + width/2 for i in x], df["Parsing_OPS"], 
                           width, label="Parsing", alpha=0.8)
    
    ax4.set_yscale("log")
    ax4.set_xlabel("ULID Libraries")
    ax4.set_ylabel("Performance (ops/sec, log scale)")
    ax4.set_title("Performance Comparison (Log Scale)", fontweight="bold")
    ax4.set_xticks(x)
    ax4.set_xticklabels(df["Library"], rotation=45, ha="right")
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("quick_benchmark_results.png", dpi=300, bbox_inches="tight")
    print("Chart saved as: quick_benchmark_results.png")

def create_summary_report(df: pd.DataFrame, results: List[Dict]) -> str:
    """Create detailed summary report without symbols."""
    
    # System info from first result
    system_info = results[0].get("system_info", {}) if results else {}
    
    report = []
    report.append("# ULID Libraries Quick Benchmark Results")
    report.append("=" * 50)
    report.append("")
    
    # System specifications
    report.append("## System Specifications")
    report.append("- CPU Cores: 8 cores")
    report.append("- Memory: 16GB total (15GB usable)")
    python_version = system_info.get('python_version', 'Unknown')
    # Extract just version and compiler, remove timestamp
    if '(' in python_version and ')' in python_version:
        # Remove everything between parentheses (timestamp)
        parts = python_version.split('(')
        version_part = parts[0].strip()
        if '[' in python_version:
            compiler_part = python_version.split('[')[1].split(']')[0]
            clean_version = f"{version_part} [{compiler_part}]"
        else:
            clean_version = version_part
    else:
        clean_version = python_version
    
    report.append(f"- Python: {clean_version}")
    report.append("- Platform: Ubuntu 20.04.6 LTS")
    report.append("")
    
    # Performance Rankings
    df_sorted = df.sort_values("Overall_Score", ascending=False)
    
    report.append("## Performance Rankings")
    report.append("")
    report.append("| Rank | Library | Generation (M ops/sec) | Parsing (M ops/sec) | Overall Score |")
    report.append("|------|---------|------------------------|---------------------|---------------|")
    
    for i, (_, row) in enumerate(df_sorted.iterrows(), 1):
        gen_ops = row["Generation_OPS"] / 1e6
        parse_ops = row["Parsing_OPS"] / 1e6
        
        report.append(f"| {i} | {row['Library']} | {gen_ops:.2f} | {parse_ops:.2f} | {row['Overall_Score']:.1f}% |")
    
    report.append("")
    
    # Library Analysis
    report.append("## Detailed Library Analysis")
    report.append("")
    
    for _, row in df_sorted.iterrows():
        report.append(f"### {row['Library']}")
        
        # Performance metrics
        gen_ops = row["Generation_OPS"]
        parse_ops = row["Parsing_OPS"]
        
        report.append("Performance:")
        report.append(f"- Generation: {gen_ops/1e6:.2f}M ops/sec ({row['Generation_Relative']:.1f}%)")
        
        if parse_ops > 0:
            report.append(f"- Parsing: {parse_ops/1e6:.2f}M ops/sec ({row['Parsing_Relative']:.1f}%)")
        else:
            report.append("- Parsing: Doesn't support with same feature")
        
        report.append("Memory Usage:")
        report.append(f"- Generation: {row['Generation_Memory_MB']:.1f}MB overhead")
        if parse_ops > 0:
            report.append(f"- Parsing: {row['Parsing_Memory_MB']:.1f}MB overhead")
        else:
            report.append("- Parsing: Doesn't support with same feature")
        
        report.append("")
    
    # Testing details
    report.append("## Test Configuration")
    report.append("- Iterations: 100,000 per test")
    report.append("- Environment: Laptop Machine")
    report.append("")
    
    return "\n".join(report)

def main():
    """Main execution function."""
    print("Starting ULID Quick Benchmark Analysis")
    print("=" * 50)
    
    # Load results
    results = load_results()
    if not results:
        print("No result files found!")
        return
    
    print(f"Loaded {len(results)} benchmark results")
    
    # Create dataframe
    df = create_performance_dataframe(results)
    df = calculate_relative_performance(df)
    
    # Create visualizations
    print("\nCreating performance visualizations...")
    create_visualizations(df)
    
    # Generate summary report
    print("\nGenerating summary report...")
    summary = create_summary_report(df, results)
    
    with open("QUICK_BENCHMARK_SUMMARY.md", "w") as f:
        f.write(summary)
    
    print("Summary saved as: QUICK_BENCHMARK_SUMMARY.md")
    
    # Print quick results to console
    print("\n" + "=" * 50)
    print("QUICK RESULTS SUMMARY")
    print("=" * 50)
    
    df_sorted = df.sort_values("Overall_Score", ascending=False)
    for i, (_, row) in enumerate(df_sorted.iterrows(), 1):
        print(f"{i}. {row['Library']}: {row['Generation_OPS']/1e6:.1f}M gen/sec, "
              f"{row['Parsing_OPS']/1e6:.1f}M parse/sec ({row['Overall_Score']:.1f}%)")
    
    print("\nChart: quick_benchmark_results.png")
    print("Report: QUICK_BENCHMARK_SUMMARY.md")
    print("Analysis complete!")

if __name__ == "__main__":
    main()