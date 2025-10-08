from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Count, Avg, Q
from django.utils import timezone
from django.db.models.functions import TruncDate
from core.models import TextAnalysis, UserFeedback, SystemMetrics
from datetime import timedelta
import csv

def dashboard_view(request):
    """Analytics dashboard with real-time data"""
    context = {
        'page_title': 'Analytics Dashboard',
    }
    return render(request, 'analytics/dashboard.html', context)

def reports_view(request):
    """Detailed reports and data analysis"""
    
    # Core Stats
    total_analyses = TextAnalysis.objects.count()
    feedback_qs = UserFeedback.objects.all()
    total_feedback = feedback_qs.count()
    feedback_rate = round((total_feedback / total_analyses) * 100, 2) if total_analyses else 0
    avg_rating = feedback_qs.aggregate(avg=Avg("rating"))["avg"] or 0

    # Predictions Distribution
    predictions = (
        TextAnalysis.objects
        .values("prediction")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    
    for p in predictions:
        p["percentage"] = round((p["count"] / total_analyses) * 100, 2) if total_analyses else 0

    # User Feedback Stars
    star_stats = []
    for star in range(5, 0, -1):
        count = feedback_qs.filter(rating=star).count()
        percentage = round((count / total_feedback) * 100, 2) if total_feedback else 0
        star_stats.append({
            "star": star,
            "count": count,
            "percentage": percentage,
        })

    # Model Performance
    model_performance = (
        TextAnalysis.objects
        .values("model_used")
        .annotate(
            count=Count("id"),
            avg_confidence=Avg("confidence_score"),
            avg_response_time=Avg("processing_time"),
        )
        .order_by("-count")
    )
    
    for m in model_performance:
        m["usage_pct"] = round((m["count"] / total_analyses) * 100, 2) if total_analyses else 0

    # Recent Activity (Last 30 days)
    today = timezone.now().date()
    last_30 = today - timedelta(days=29)

    activity_qs = (
        TextAnalysis.objects
        .filter(created_at__date__gte=last_30)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )

    labels, data = [], []
    for i in range(30):
        day = last_30 + timedelta(days=i)
        labels.append(day.strftime("%Y-%m-%d"))
        match = next((a for a in activity_qs if a["day"] == day), None)
        data.append(match["count"] if match else 0)

    context = {
        "total_analyses": total_analyses,
        "feedback_stats": {
            "total_feedback": total_feedback,
            "avg_rating": round(avg_rating, 1),
        },
        "feedback_rate": feedback_rate,
        "predictions": predictions,
        "star_stats": star_stats,
        "model_performance": model_performance,
        "recent_activity_labels": labels,
        "recent_activity_data": data,
    }

    return render(request, "analytics/reports.html", context)

def export_data(request):
    """Export analytics data to CSV"""
    export_type = request.GET.get('type', 'analyses')
    response = HttpResponse(content_type='text/csv')

    if export_type == 'analyses':
        response['Content-Disposition'] = 'attachment; filename="analyses.csv"'
        writer = csv.writer(response)
        
        writer.writerow([
            'ID', 'Date', 'Prediction', 'Confidence', 'Model Used',
            'Processing Time', 'Text Length', 'Has Feedback'
        ])

        analyses = TextAnalysis.objects.all().order_by('-created_at')
        for analysis in analyses:
            writer.writerow([
                str(analysis.id),
                analysis.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                analysis.prediction,
                analysis.confidence_score,
                analysis.model_used,
                analysis.processing_time,
                analysis.text_length,
                hasattr(analysis, 'feedback'),
            ])

    elif export_type == 'feedback':
        response['Content-Disposition'] = 'attachment; filename="feedback.csv"'
        writer = csv.writer(response)
        
        writer.writerow([
            'ID', 'Date', 'Rating', 'Analysis ID',
            'Prediction', 'Confidence', 'Feedback Text'
        ])

        feedback = UserFeedback.objects.select_related('analysis').order_by('-created_at')
        for fb in feedback:
            writer.writerow([
                fb.id,
                fb.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                fb.rating,
                str(fb.analysis.id),
                fb.analysis.prediction,
                fb.analysis.confidence_score,
                fb.feedback_text or "",
            ])

    return response