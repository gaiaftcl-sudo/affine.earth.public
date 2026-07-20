import os
import sys
import click
import time
from ..core.types import LLMModelConfig, LLVMCompilerConfig, BenchmarkReport
from ..core.reporter import Reporter
from ..llm.runner import LLMRunner
from ..llm.suites import get_suite, LIST_OF_SUITES
from ..llvm.runner import LLVMRunner
from ..llvm.benchmarks import LIST_OF_LLVM_BENCHMARKS
from ..web.server import start_dashboard_server

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """LLM & LLVM Benchmark Testing Suite (llm-llvm-bench)"""
    pass

@cli.group()
def llm():
    """LLM Evaluation Commands"""
    pass

@llm.command(name="run")
@click.option("--models", default="mock", help="Comma-separated model names or configs")
@click.option("--provider", default="mock", help="Provider type: mock, openai, anthropic, ollama")
@click.option("--suites", default="code,reasoning,tool_use", help="Comma-separated suite names: code,reasoning,tool_use")
@click.option("--endpoint", default=None, help="Custom REST API endpoint URL")
@click.option("--api-key", default=None, help="API key for provider")
@click.option("--out", default="reports/llm_benchmark.json", help="Output JSON path")
def llm_run(models, provider, suites, endpoint, api_key, out):
    """Run LLM evaluation suites across real-world domains"""
    click.echo("🚀 Starting LLM Real-World Domain Benchmark...")

    model_list = [m.strip() for m in models.split(",") if m.strip()]
    suite_list = [s.strip() for s in suites.split(",") if s.strip()]

    report = BenchmarkReport(report_id=f"llm_run_{int(time.time())}")

    for model_name in model_list:
        cfg = LLMModelConfig(
            name=model_name,
            provider=provider,
            endpoint=endpoint,
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
        )
        runner = LLMRunner(cfg)

        for s_name in suite_list:
            samples = get_suite(s_name)
            click.echo(f"  -> Running model '{model_name}' on suite '{s_name}' ({len(samples)} samples)...")
            res = runner.run_suite(s_name, samples)
            report.llm_suites.append(res)
            click.echo(f"     ✅ Done! Accuracy: {res.accuracy_pct:.1f}% | Latency: {res.avg_latency_sec:.3f}s | {res.tokens_per_sec:.1f} t/s")

    Reporter.save_json(report, out)
    md_out = os.path.splitext(out)[0] + ".md"
    Reporter.save_markdown(report, md_out)
    click.echo(f"📊 Report saved to {out} and {md_out}")

@cli.group()
def llvm():
    """LLVM Compiler Benchmark Commands"""
    pass

@llvm.command(name="run")
@click.option("--opt-levels", default="-O0,-O2,-O3,-Os", help="Comma-separated opt levels: -O0,-O2,-O3,-Os")
@click.option("--compiler", default="clang", help="Compiler executable path")
@click.option("--out", default="reports/llvm_benchmark.json", help="Output JSON path")
def llvm_run(opt_levels, compiler, out):
    """Run LLVM compiler performance benchmarks"""
    click.echo("⚙️ Starting LLVM Compiler Performance Benchmark...")

    opts = [o.strip() for o in opt_levels.split(",") if o.strip()]
    report = BenchmarkReport(report_id=f"llvm_run_{int(time.time())}")

    for opt in opts:
        cfg = LLVMCompilerConfig(name=f"clang-{opt}", compiler_path=compiler, opt_level=opt)
        runner = LLVMRunner(cfg)
        click.echo(f"  -> Running LLVM compiler '{compiler}' with '{opt}'...")
        res = runner.run_suite(f"llvm_suite_{opt}", LIST_OF_LLVM_BENCHMARKS)
        report.llvm_suites.append(res)
        click.echo(f"     ✅ Done! Avg Compile Time: {res.avg_compile_time_sec:.4f}s | Text Size: {res.total_text_size_bytes:,} B")

    Reporter.save_json(report, out)
    md_out = os.path.splitext(out)[0] + ".md"
    Reporter.save_markdown(report, md_out)
    click.echo(f"📊 Report saved to {out} and {md_out}")

@cli.command(name="serve")
@click.option("--port", default=8888, help="Web dashboard port")
@click.option("--host", default="127.0.0.1", help="Web dashboard host")
def serve(port, host):
    """Launch interactive LLM & LLVM benchmark web dashboard"""
    start_dashboard_server(host=host, port=port)

if __name__ == "__main__":
    cli()
