
import argparse

from rich.console import Console
from rich.table import Table

from .config import load_config
from .providers import (
    DemoProvider,
    GreenhouseProvider,
    PortalSearchLinks,
)
from .matcher import score_job
from .storage import Store
from .report import daily_report


console = Console()


def create_provider(cfg):
    """
    Create the configured job discovery provider.

    Supported:
        demo
        greenhouse
    """

    search_config = cfg["search"]

    provider_name = search_config.get(
        "provider",
        "demo",
    ).lower()

    if provider_name == "demo":

        console.print(
            "[yellow]Using demo job provider[/yellow]"
        )

        return DemoProvider()

    elif provider_name == "greenhouse":

        board_tokens = search_config.get(
            "greenhouse_board_tokens",
            [],
        )

        if not board_tokens:

            console.print(
                "[yellow]No Greenhouse board tokens configured.[/yellow]"
            )

            console.print(
                "Add employer board tokens under "
                "search.greenhouse_board_tokens in config.yaml"
            )

        console.print(
            "[green]Using Greenhouse public job-board provider[/green]"
        )

        return GreenhouseProvider(
            board_tokens=board_tokens
        )

    else:

        raise ValueError(
            f"Unsupported job provider: {provider_name}"
        )


def show_portal_links(cfg):
    """
    Generate LinkedIn and Naukri search URLs.

    These URLs allow the user to open job searches.
    They do not scrape or submit applications.
    """

    search_config = cfg["search"]

    keywords = search_config.get(
        "keywords",
        [],
    )

    locations = cfg["profile"].get(
        "target_locations",
        [],
    )

    links = PortalSearchLinks.build(
        keywords,
        locations,
    )

    table = Table(
        title="LinkedIn and Naukri Job Search Links"
    )

    table.add_column(
        "Portal",
        style="cyan",
    )

    table.add_column(
        "Job Title",
    )

    table.add_column(
        "Location",
    )

    table.add_column(
        "Search URL",
    )

    for item in links:

        table.add_row(
            item["source"],
            item["keyword"],
            item["location"],
            item["url"],
        )

    console.print(table)


def discover_jobs(cfg, store):
    """
    Discover jobs, calculate matching scores,
    and save results to SQLite.
    """

    profile = cfg["profile"]

    search_config = cfg["search"]

    provider = create_provider(cfg)

    keywords = search_config.get(
        "keywords",
        [],
    )

    locations = profile.get(
        "target_locations",
        [],
    )

    max_jobs = search_config.get(
        "max_jobs_per_run",
        50,
    )

    min_score = search_config.get(
        "min_match_score",
        50,
    )

    console.print(
        "\n[bold]Searching for jobs...[/bold]\n"
    )

    jobs = provider.search(
        keywords,
        locations,
        max_jobs,
    )

    table = Table(
        title="Job Matches"
    )

    table.add_column(
        "ID",
        style="cyan",
    )

    table.add_column(
        "Title",
    )

    table.add_column(
        "Company",
    )

    table.add_column(
        "Location",
    )

    table.add_column(
        "Score",
    )

    table.add_column(
        "Matched Skills",
    )

    matched_count = 0

    for job in jobs:

        result = score_job(
            job,
            profile,
        )

        score = result["score"]

        matched_skills = result[
            "matched_skills"
        ]

        status = (
            "matched"
            if score >= min_score
            else "low_match"
        )

        notes = (
            f"Matched: {', '.join(matched_skills)}"
        )

        store.add(
            job,
            score,
            status,
            notes,
        )

        if score >= min_score:

            matched_count += 1

            table.add_row(
                job.id,
                job.title,
                job.company,
                job.location,
                str(score),
                ", ".join(matched_skills),
            )

    console.print(table)

    console.print(
        f"\nJobs discovered: {len(jobs)}"
    )

    console.print(
        f"Jobs matching your criteria: {matched_count}"
    )

    console.print(
        f"Minimum matching score: {min_score}"
    )

    console.print(
        "\n[green]Discovery completed.[/green]"
    )

    console.print(
        "Use the report command to export today's results."
    )

    return jobs


def approve_job(args, store):
    """
    Mark a job approved for review.

    This does not submit an application.
    """

    if not args.job_id:

        console.print(
            "[red]Please provide a job ID.[/red]"
        )

        return

    rows = store.rows()

    row = next(
        (
            item
            for item in rows
            if item[0] == args.job_id
        ),
        None,
    )

    if not row:

        console.print(
            "[red]Job ID not found.[/red]"
        )

        return

    console.print(
        "\n[bold]Job Details[/bold]"
    )

    console.print(
        f"Title: {row[1]}"
    )

    console.print(
        f"Company: {row[2]}"
    )

    console.print(
        f"Location: {row[3]}"
    )

    console.print(
        f"URL: {row[4]}"
    )

    console.print(
        f"Matching score: {row[5]}"
    )

    console.print(
        "\nApproval allows the job to proceed to review."
    )

    console.print(
        "It does not submit an application."
    )

    confirmation = input(
        "\nType REVIEW to approve for manual review: "
    ).strip()

    if confirmation != "REVIEW":

        console.print(
            "[yellow]Approval cancelled.[/yellow]"
        )

        return

    store.update_status(
        args.job_id,
        "approved_for_review",
        "User approved review; submission remains manual",
    )

    console.print(
        "\n[green]Job approved for review.[/green]"
    )

    console.print(
        "No application was submitted."
    )


def generate_report(cfg, store):
    """
    Generate the daily CSV report.
    """

    report_dir = cfg["workflow"].get(
        "report_dir",
        "./reports",
    )

    path, counts = daily_report(
        store,
        report_dir,
    )

    console.print(
        f"\n[green]Daily report generated:[/green] {path}"
    )

    console.print(
        "\n[bold]Application Status Summary[/bold]"
    )

    if counts:

        for status, count in counts.items():

            console.print(
                f"{status}: {count}"
            )

    else:

        console.print(
            "No applications recorded today."
        )


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Python AI Job Application Assistant"
        )
    )

    parser.add_argument(
        "command",
        choices=[
            "discover",
            "report",
            "approve",
            "links",
        ],
        help=(
            "discover jobs, generate reports, "
            "approve jobs, or show portal links"
        ),
    )

    parser.add_argument(
        "--job-id",
        help="Job ID for the approve command",
    )

    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Use deterministic matching only",
    )

    args = parser.parse_args()

    cfg = load_config()

    store = Store(
        cfg["workflow"]["database_path"]
    )

    if args.command == "report":

        generate_report(
            cfg,
            store,
        )

        return

    if args.command == "approve":

        approve_job(
            args,
            store,
        )

        return

    if args.command == "links":

        show_portal_links(
            cfg,
        )

        return

    if args.command == "discover":

        discover_jobs(
            cfg,
            store,
        )

        # Show portal searches after discovery.
        show_portal_links(
            cfg,
        )

        console.print(
            "\n[bold green]Job discovery finished.[/bold green]"
        )

        console.print(
            "\nNext commands:"
        )

        console.print(
            "Generate report: "
            "python -m job_assistant.cli report"
        )

        console.print(
            "Show portal links: "
            "python -m job_assistant.cli links"
        )

        console.print(
            "Approve job: "
            "python -m job_assistant.cli approve --job-id JOB_ID"
        )


if __name__ == "__main__":

    main()
