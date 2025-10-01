from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Avg, Q
from django.utils import timezone
from core.models import TextAnalysis, UserFeedback, SystemMetrics
from datetime import datetime, timedelta
import csv
import json
from django.shortcuts import render
from django.db.models import Count, Avg
from django.utils import timezone
from django.db.models.functions import TruncDate
from .models import Analysis, Feedback
from datetime import timedelta

def dashboard_view(request):
    """Analytics dashboard with charts and statistics"""
    
    context = {
        'page_title': 'Analytics Dashboard',
    }
    
    return render(request, 'analytics/dashboard.html', context)

# def reports_view(request):
#     """Detailed reports and data analysis"""
    
#     # Calculate various metrics
#     total_analyses = TextAnalysis.objects.count()
    
#     # Prediction breakdown
#     predictions = TextAnalysis.objects.values('prediction').annotate(
#         count=Count('prediction')
#     ).order_by('-count')
    
#     # Model performance
#     model_performance = TextAnalysis.objects.values('model_used').annotate(
#         count=Count('model_used'),
#         avg_confidence=Avg('confidence_score'),
#         avg_response_time=Avg('processing_time')
#     ).order_by('-count')
    
#     # User feedback analysis
#     feedback_stats = UserFeedback.objects.aggregate(
#         total_feedback=Count('id'),
#         avg_rating=Avg('rating'),
#         five_star=Count('id', filter=Q(rating=5)),
#         four_star=Count('id', filter=Q(rating=4)),
#         three_star=Count('id', filter=Q(rating=3)),
#         two_star=Count('id', filter=Q(rating=2)),
#         one_star=Count('id', filter=Q(rating=1)),
#     )
    
#     # Recent activity (last 30 days)
#     thirty_days_ago = timezone.now() - timedelta(days=30)
#     recent_activity = []
    
#     for i in range(30):
#         date = (timezone.now() - timedelta(days=i)).date()
#         daily_count = TextAnalysis.objects.filter(created_at__date=date).count()
#         recent_activity.append({
#             'date': date.strftime('%Y-%m-%d'),
#             'count': daily_count
#         })
    
#     recent_activity.reverse()
    
#     context = {
#         'page_title': 'Detailed Reports',
#         'total_analyses': total_analyses,
#         'predictions': predictions,
#         'model_performance': model_performance,
#         'feedback_stats': feedback_stats,
#         'recent_activity': recent_activity,
#         'feedback_rate': round((feedback_stats['total_feedback'] / max(total_analyses, 1)) * 100, 1),
#     }
    
#     return render(request, 'analytics/reports.html', context)

def reports_view(request):
    # ----- Core Stats -----
    total_analyses = Analysis.objects.count()
    feedback_qs = Feedback.objects.all()
    total_feedback = feedback_qs.count()
    feedback_rate = round((total_feedback / total_analyses) * 100, 2) if total_analyses else 0
    avg_rating = feedback_qs.aggregate(avg=Avg("rating"))["avg"] or 0

    # ----- Predictions Distribution -----
    predictions = (
        Analysis.objects.values("prediction")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    # add percentages
    for p in predictions:
        p["percentage"] = round((p["count"] / total_analyses) * 100, 2) if total_analyses else 0

    # ----- User Feedback Stars -----
    star_stats = []
    for star in range(5, 0, -1):  # 5 → 1
        count = feedback_qs.filter(rating=star).count()
        percentage = round((count / total_feedback) * 100, 2) if total_feedback else 0
        star_stats.append({
            "star": star,
            "count": count,
            "percentage": percentage,
        })

    # ----- Model Performance -----
    model_performance = (
        Analysis.objects.values("model_used")
        .annotate(
            count=Count("id"),
            avg_confidence=Avg("confidence"),
            avg_response_time=Avg("response_time"),
        )
        .order_by("-count")
    )
    for m in model_performance:
        m["usage_pct"] = round((m["count"] / total_analyses) * 100, 2) if total_analyses else 0

    # ----- Recent Activity (Last 30 days) -----
    today = timezone.now().date()
    last_30 = today - timedelta(days=29)

    activity_qs = (
        Analysis.objects.filter(created_at__date__gte=last_30)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )

    # build daily series (ensures days with zero are included)
    labels, data = [], []
    for i in range(30):
        day = last_30 + timedelta(days=i)
        labels.append(day.strftime("%Y-%m-%d"))
        match = next((a for a in activity_qs if a["day"] == day), None)
        data.append(match["count"] if match else 0)

    # ----- Context -----
    context = {
        "total_analyses": total_analyses,
        "feedback_stats": {
            "total_feedback": total_feedback,
            "avg_rating": avg_rating,
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

        # Header
        writer.writerow([
            'ID', 'Date', 'Prediction', 'Confidence', 'Model Used',
            'Response Time', 'Text Length', 'Has Feedback'
        ])

        # Data
        analyses = Analysis.objects.all().order_by('-created_at')
        for analysis in analyses:
            writer.writerow([
                str(analysis.id),
                analysis.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                analysis.prediction,
                analysis.confidence,
                analysis.model_used,
                analysis.response_time,
                analysis.text_length,
                analysis.feedbacks.exists(),  # ✅ uses related_name
            ])

    elif export_type == 'feedback':
        response['Content-Disposition'] = 'attachment; filename="feedback.csv"'
        writer = csv.writer(response)

        # Header
        writer.writerow([
            'ID', 'Date', 'Rating', 'Analysis ID',
            'Prediction', 'Confidence', 'Feedback Text'
        ])

        # Data
        feedback = Feedback.objects.select_related('analysis').order_by('-created_at')
        for fb in feedback:
            writer.writerow([
                fb.id,
                fb.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                fb.rating,
                str(fb.analysis.id),
                fb.analysis.prediction,
                fb.analysis.confidence,
                fb.feedback_text or "",
            ])

    return response
