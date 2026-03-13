"""
Metrics aggregation for autonomous-glm dashboard.

Collects and computes audit statistics from the database.
"""

from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class Period(str, Enum):
    """Time period for metrics aggregation."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    ALL = "all"


class FindingsSummary(BaseModel):
    """Summary of findings by severity."""
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    total: int = 0


class TrendPoint(BaseModel):
    """A single point in a trend chart."""
    date: str  # ISO date string (YYYY-MM-DD)
    audits: int = 0
    findings: int = 0


class TrendData(BaseModel):
    """Historical trend data."""
    points: list[TrendPoint] = Field(default_factory=list)
    period_days: int = 7


class ArtifactStats(BaseModel):
    """Statistics about processed artifacts."""
    total_screens: int = 0
    total_flows: int = 0
    total_components: int = 0
    total_tokens: int = 0


class DimensionBreakdown(BaseModel):
    """Findings breakdown by audit dimension."""
    dimension: str
    count: int
    percentage: float


class DashboardMetrics(BaseModel):
    """Complete dashboard metrics."""
    period: Period
    period_start: str  # ISO datetime
    period_end: str  # ISO datetime
    
    # Audit counts
    total_audits: int = 0
    successful_audits: int = 0
    failed_audits: int = 0
    
    # Findings
    findings_summary: FindingsSummary = Field(default_factory=FindingsSummary)
    severity_distribution: dict[str, int] = Field(default_factory=dict)
    dimension_breakdown: list[DimensionBreakdown] = Field(default_factory=list)
    
    # Trends
    trend_data: TrendData = Field(default_factory=TrendData)
    
    # Artifacts
    artifact_stats: ArtifactStats = Field(default_factory=ArtifactStats)


class MetricsAggregator:
    """Aggregates audit metrics from the database.
    
    Example:
        >>> aggregator = MetricsAggregator()
        >>> metrics = aggregator.get_metrics(Period.WEEK)
        >>> print(metrics.total_audits)
        47
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the aggregator.
        
        Args:
            db_path: Optional path to the database file
        """
        self.db_path = db_path
    
    def get_period_range(self, period: Period) -> tuple[datetime, datetime]:
        """Get the date range for a period.
        
        Args:
            period: Time period enum value
            
        Returns:
            Tuple of (start_datetime, end_datetime)
        """
        now = datetime.now()
        
        if period == Period.DAY:
            start = now - timedelta(days=1)
        elif period == Period.WEEK:
            start = now - timedelta(weeks=1)
        elif period == Period.MONTH:
            start = now - timedelta(days=30)
        else:  # ALL
            start = datetime(2020, 1, 1)  # Far enough in the past
        
        return start, now
    
    def get_metrics(self, period: Period = Period.WEEK) -> DashboardMetrics:
        """Get complete dashboard metrics for a period.
        
        Args:
            period: Time period to aggregate over
            
        Returns:
            DashboardMetrics with all aggregated data
        """
        start, end = self.get_period_range(period)
        
        return DashboardMetrics(
            period=period,
            period_start=start.isoformat(),
            period_end=end.isoformat(),
            total_audits=self.get_audit_count(period),
            successful_audits=self._get_audits_by_status("completed", period),
            failed_audits=self._get_audits_by_status("failed", period),
            findings_summary=self.get_findings_summary(period),
            severity_distribution=self.get_severity_distribution(period),
            dimension_breakdown=self.get_dimension_breakdown(period),
            trend_data=self.get_trend_data(7 if period == Period.WEEK else 30),
            artifact_stats=self.get_artifact_stats(),
        )
    
    def get_audit_count(self, period: Period = Period.WEEK) -> int:
        """Get total audit count for a period.
        
        Args:
            period: Time period to aggregate over
            
        Returns:
            Number of audits in the period
        """
        from src.db.database import connection
        
        start, end = self.get_period_range(period)
        
        with connection(self.db_path) as conn:
            if period == Period.ALL:
                cursor = conn.execute("SELECT COUNT(*) as count FROM audit_sessions")
            else:
                cursor = conn.execute(
                    """SELECT COUNT(*) as count FROM audit_sessions 
                       WHERE created_at >= ? AND created_at <= ?""",
                    (start.isoformat(), end.isoformat()),
                )
            row = cursor.fetchone()
        
        return row["count"] if row else 0
    
    def _get_audits_by_status(self, status: str, period: Period) -> int:
        """Get audit count by status for a period.
        
        Args:
            status: Audit status to count
            period: Time period to aggregate over
            
        Returns:
            Number of audits with the given status
        """
        from src.db.database import connection
        
        start, end = self.get_period_range(period)
        
        with connection(self.db_path) as conn:
            if period == Period.ALL:
                cursor = conn.execute(
                    """SELECT COUNT(*) as count FROM audit_sessions 
                       WHERE status = ?""",
                    (status,),
                )
            else:
                cursor = conn.execute(
                    """SELECT COUNT(*) as count FROM audit_sessions 
                       WHERE status = ? AND created_at >= ? AND created_at <= ?""",
                    (status, start.isoformat(), end.isoformat()),
                )
            row = cursor.fetchone()
        
        return row["count"] if row else 0
    
    def get_findings_summary(self, period: Period = Period.WEEK) -> FindingsSummary:
        """Get findings summary by severity for a period.
        
        Args:
            period: Time period to aggregate over
            
        Returns:
            FindingsSummary with counts by severity
        """
        from src.db.database import connection
        
        start, end = self.get_period_range(period)
        
        with connection(self.db_path) as conn:
            # Query findings joined with severity reference table
            if period == Period.ALL:
                cursor = conn.execute(
                    """SELECT s.name as severity, COUNT(*) as count
                       FROM audit_findings af
                       JOIN severities s ON af.severity_id = s.id
                       GROUP BY s.name"""
                )
            else:
                cursor = conn.execute(
                    """SELECT s.name as severity, COUNT(*) as count
                       FROM audit_findings af
                       JOIN severities s ON af.severity_id = s.id
                       WHERE af.created_at >= ? AND af.created_at <= ?
                       GROUP BY s.name""",
                    (start.isoformat(), end.isoformat()),
                )
            rows = cursor.fetchall()
        
        summary = FindingsSummary()
        for row in rows:
            severity = row["severity"].lower()
            count = row["count"]
            if severity == "critical":
                summary.critical = count
            elif severity == "high":
                summary.high = count
            elif severity == "medium":
                summary.medium = count
            elif severity == "low":
                summary.low = count
            summary.total += count
        
        return summary
    
    def get_severity_distribution(self, period: Period = Period.WEEK) -> dict[str, int]:
        """Get severity distribution for a period.
        
        Args:
            period: Time period to aggregate over
            
        Returns:
            Dictionary mapping severity name to count
        """
        summary = self.get_findings_summary(period)
        return {
            "critical": summary.critical,
            "high": summary.high,
            "medium": summary.medium,
            "low": summary.low,
        }
    
    def get_dimension_breakdown(self, period: Period = Period.WEEK) -> list[DimensionBreakdown]:
        """Get findings breakdown by audit dimension.
        
        Args:
            period: Time period to aggregate over
            
        Returns:
            List of DimensionBreakdown objects sorted by count descending
        """
        from src.db.database import connection
        
        start, end = self.get_period_range(period)
        
        with connection(self.db_path) as conn:
            # Query findings by dimension (stored in metadata JSON)
            if period == Period.ALL:
                cursor = conn.execute(
                    """SELECT 
                         COALESCE(
                           JSON_EXTRACT(metadata, '$.dimension'),
                           JSON_EXTRACT(metadata, '$.audit_dimension'),
                           'unknown'
                         ) as dimension,
                         COUNT(*) as count
                       FROM audit_findings
                       WHERE metadata IS NOT NULL
                       GROUP BY dimension
                       ORDER BY count DESC"""
                )
            else:
                cursor = conn.execute(
                    """SELECT 
                         COALESCE(
                           JSON_EXTRACT(metadata, '$.dimension'),
                           JSON_EXTRACT(metadata, '$.audit_dimension'),
                           'unknown'
                         ) as dimension,
                         COUNT(*) as count
                       FROM audit_findings
                       WHERE metadata IS NOT NULL
                         AND created_at >= ? AND created_at <= ?
                       GROUP BY dimension
                       ORDER BY count DESC""",
                    (start.isoformat(), end.isoformat()),
                )
            rows = cursor.fetchall()
        
        # Calculate total for percentage
        total = sum(row["count"] for row in rows)
        
        breakdown = []
        for row in rows:
            dimension = row["dimension"] or "unknown"
            # Clean up dimension string (remove quotes if present)
            dimension = dimension.strip('"').strip("'")
            count = row["count"]
            percentage = (count / total * 100) if total > 0 else 0.0
            
            breakdown.append(DimensionBreakdown(
                dimension=dimension,
                count=count,
                percentage=round(percentage, 1),
            ))
        
        return breakdown
    
    def get_trend_data(self, days: int = 7) -> TrendData:
        """Get historical trend data for a number of days.
        
        Args:
            days: Number of days to include in trend
            
        Returns:
            TrendData with daily points
        """
        from src.db.database import connection
        
        end = datetime.now()
        start = end - timedelta(days=days)
        
        points = []
        
        with connection(self.db_path) as conn:
            # Get daily audit counts
            cursor = conn.execute(
                """SELECT DATE(created_at) as day, COUNT(*) as count
                   FROM audit_sessions
                   WHERE created_at >= ? AND created_at <= ?
                   GROUP BY day
                   ORDER BY day""",
                (start.isoformat(), end.isoformat()),
            )
            audit_rows = {row["day"]: row["count"] for row in cursor.fetchall()}
            
            # Get daily finding counts
            cursor = conn.execute(
                """SELECT DATE(created_at) as day, COUNT(*) as count
                   FROM audit_findings
                   WHERE created_at >= ? AND created_at <= ?
                   GROUP BY day
                   ORDER BY day""",
                (start.isoformat(), end.isoformat()),
            )
            finding_rows = {row["day"]: row["count"] for row in cursor.fetchall()}
        
        # Generate points for each day in range
        current = start.date()
        end_date = end.date()
        
        while current <= end_date:
            date_str = current.isoformat()
            points.append(TrendPoint(
                date=date_str,
                audits=audit_rows.get(date_str, 0),
                findings=finding_rows.get(date_str, 0),
            ))
            current += timedelta(days=1)
        
        return TrendData(points=points, period_days=days)
    
    def get_artifact_stats(self) -> ArtifactStats:
        """Get statistics about processed artifacts.
        
        Returns:
            ArtifactStats with counts of all artifact types
        """
        from src.db.database import connection
        
        with connection(self.db_path) as conn:
            # Count screens
            cursor = conn.execute("SELECT COUNT(*) as count FROM screens")
            screens = cursor.fetchone()["count"]
            
            # Count flows
            cursor = conn.execute("SELECT COUNT(*) as count FROM flows")
            flows = cursor.fetchone()["count"]
            
            # Count components
            cursor = conn.execute("SELECT COUNT(*) as count FROM components")
            components = cursor.fetchone()["count"]
            
            # Count tokens
            cursor = conn.execute("SELECT COUNT(*) as count FROM system_tokens")
            tokens = cursor.fetchone()["count"]
        
        return ArtifactStats(
            total_screens=screens,
            total_flows=flows,
            total_components=components,
            total_tokens=tokens,
        )