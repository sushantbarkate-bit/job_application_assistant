import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from .config import load_config
from .providers import DemoProvider
from .matcher import score_job
from .storage import Store
from .report import daily_report

console = Console()

def main():
    parser = argparse.ArgumentParser(description="AI Job Application Assistant (approval-first)")
    parser.add_argument("command", choices=["discover", "report", "approve"], help="discover jobs, report, or review a match")
    parser.add_argument("--job-id", help="Job ID for approve command")
    parser.add_argument("--no-ai", action="store_true", help="Use deterministic matching only")
    args = parser.parse_args()
    cfg = load_config()
    store = Store(cfg["workflow"]["database_path"])

    if args.command == "report":
        path, counts = daily_report(store, cfg["workflow"]["report_dir"])
        console.print(f"Daily report: [green]{path}[/green]")
        console.print(counts or "No applications recorded today.")
        return

    if args.command == "approve":
        if not args.job_id:
            parser.error("approve requires --job-id")
        row = next((r for r in store.rows() if r[0] == args.job_id), None)
        if not row:
            console.print("Job ID not found.", style="red")
            return
        console.print(f"[bold]{row[1]}[/bold] at {row[2]} — {row[4]}")
        console.print("Approval means you may proceed to review/fill the application. This command does not submit.")
        if input("Type REVIEW to mark ready for manual review: ").strip() == "REVIEW":
            store.update_status(args.job_id, "approved_for_review", "User approved review; submission still manual")
            console.print("Marked approved_for_review. No application was submitted.", style="green")
        return

    provider = DemoProvider()
    jobs = provider.search(cfg["search"]["keywords"], cfg["profile"]["target_locations"], cfg["search"]["max_jobs_per_run"])
    table = Table(title="Job matches (demo provider)")
    for col in ["ID", "Title", "Company", "Location", "Score", "Matched skills"]:
        table.add_column(col)
    min_score = cfg["search"]["min_match_score"]
    for job in jobs:
        result = score_job(job, cfg["profile"])
        store.add(job, result["score"], "matched" if result["score"] >= min_score else "low_match",
                  f"Matched: {', '.join(result['matched_skills'])}")
        if result["score"] >= min_score:
            table.add_row(job.id, job.title, job.company, job.location, str(result["score"]), ", ".join(result["matched_skills"]))
    console.print(table)
    console.print("\nDiscovery complete. Demo data only; connect a permitted provider for live jobs.")
    console.print("Use `python -m job_assistant.cli report` to export today's CSV.")

if __name__ == "__main__":
    main()
