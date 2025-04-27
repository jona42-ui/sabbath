from app import celery, db
from app.models.user import User, SpiritualRecord
from app.utils.monitoring import track_resource_usage
from app.utils.doctrinal import DoctrinalAnalyzer
from datetime import datetime, timedelta
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import numpy as np

@celery.task
@track_resource_usage('analyze_spiritual_growth')
def analyze_spiritual_growth(user_id):
    """Analyze user's spiritual growth patterns"""
    try:
        # Get user's spiritual records
        records = SpiritualRecord.query.filter_by(user_id=user_id).all()
        
        if not records:
            return {'status': 'no_data'}
        
        # Convert records to DataFrame
        data = []
        for record in records:
            metrics = record.metrics
            data.append({
                'date': record.date,
                'bible_study_minutes': metrics.get('bible_study', {}).get('duration', 0),
                'prayer_minutes': metrics.get('prayer', {}).get('duration', 0),
                'service_hours': metrics.get('service', {}).get('hours', 0),
                'meditation_minutes': metrics.get('meditation', {}).get('duration', 0)
            })
        
        df = pd.DataFrame(data)
        
        # Calculate trends
        trends = calculate_growth_trends(df)
        
        # Identify growth patterns
        patterns = identify_growth_patterns(df)
        
        # Generate personalized insights
        insights = generate_insights(trends, patterns)
        
        # Store analysis results
        user = User.query.get(user_id)
        if user:
            user.profile['growth_analysis'] = {
                'last_updated': datetime.utcnow().isoformat(),
                'trends': trends,
                'patterns': patterns,
                'insights': insights
            }
            db.session.commit()
        
        return {
            'status': 'success',
            'trends': trends,
            'patterns': patterns,
            'insights': insights
        }
    except Exception as e:
        celery.logger.error(f"Error analyzing spiritual growth: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@celery.task
def generate_weekly_report(user_id):
    """Generate weekly spiritual growth report"""
    try:
        user = User.query.get(user_id)
        if not user:
            return {'status': 'error', 'message': 'User not found'}
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        # Get weekly records
        records = SpiritualRecord.query.filter(
            SpiritualRecord.user_id == user_id,
            SpiritualRecord.date >= start_date,
            SpiritualRecord.date <= end_date
        ).all()
        
        # Analyze weekly progress
        weekly_stats = calculate_weekly_stats(records)
        
        # Generate recommendations
        recommendations = generate_recommendations(weekly_stats, user.profile)
        
        # Store report
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'stats': weekly_stats,
            'recommendations': recommendations
        }
        
        user.profile['latest_weekly_report'] = report
        db.session.commit()
        
        return {
            'status': 'success',
            'report': report
        }
    except Exception as e:
        celery.logger.error(f"Error generating weekly report: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@celery.task
def analyze_prayer_patterns(user_id):
    """Analyze prayer patterns and effectiveness"""
    try:
        # Get user's prayer records
        records = PrayerRequest.query.filter_by(user_id=user_id).all()
        
        if not records:
            return {'status': 'no_data'}
        
        # Analyze patterns
        patterns = {
            'total_requests': len(records),
            'answered_prayers': sum(1 for r in records if r.is_answered),
            'avg_answer_time': calculate_avg_answer_time(records),
            'common_themes': extract_prayer_themes(records),
            'peak_prayer_times': analyze_prayer_times(records)
        }
        
        # Generate spiritual insights
        doctrinal_analyzer = DoctrinalAnalyzer()
        insights = doctrinal_analyzer.analyze_prayer_patterns(patterns)
        
        return {
            'status': 'success',
            'patterns': patterns,
            'insights': insights
        }
    except Exception as e:
        celery.logger.error(f"Error analyzing prayer patterns: {str(e)}")
        return {'status': 'error', 'message': str(e)}

def calculate_growth_trends(df):
    """Calculate spiritual growth trends from DataFrame"""
    trends = {}
    
    for column in df.columns:
        if column != 'date':
            # Calculate moving averages
            trends[column] = {
                'weekly_avg': df[column].rolling(window=7).mean().tolist(),
                'monthly_avg': df[column].rolling(window=30).mean().tolist(),
                'trend': calculate_trend_direction(df[column])
            }
    
    return trends

def identify_growth_patterns(df):
    """Identify patterns in spiritual growth data"""
    # Prepare data for clustering
    features = df.drop('date', axis=1)
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)
    
    # Perform clustering
    kmeans = KMeans(n_clusters=3, random_state=42)
    clusters = kmeans.fit_predict(scaled_features)
    
    # Analyze clusters
    patterns = []
    for i in range(3):
        cluster_data = features[clusters == i]
        patterns.append({
            'cluster': i,
            'size': len(cluster_data),
            'avg_metrics': cluster_data.mean().to_dict(),
            'characteristics': identify_cluster_characteristics(cluster_data)
        })
    
    return patterns

def generate_insights(trends, patterns):
    """Generate personalized spiritual insights"""
    insights = []
    
    # Analyze trends
    for metric, data in trends.items():
        if data['trend'] == 'increasing':
            insights.append(f"Your {metric} is showing positive growth")
        elif data['trend'] == 'decreasing':
            insights.append(f"Your {metric} might need more attention")
    
    # Analyze patterns
    for pattern in patterns:
        if pattern['size'] > 0:
            characteristics = pattern['characteristics']
            insights.append(
                f"We noticed a pattern of {characteristics['primary_focus']} "
                f"with {characteristics['secondary_focus']}"
            )
    
    return insights

def calculate_trend_direction(series):
    """Calculate trend direction using linear regression"""
    x = np.arange(len(series))
    slope = np.polyfit(x, series, 1)[0]
    
    if slope > 0.1:
        return 'increasing'
    elif slope < -0.1:
        return 'decreasing'
    else:
        return 'stable'

def identify_cluster_characteristics(cluster_data):
    """Identify main characteristics of a cluster"""
    means = cluster_data.mean()
    primary_focus = means.idxmax()
    secondary_focus = means.drop(primary_focus).idxmax()
    
    return {
        'primary_focus': primary_focus,
        'secondary_focus': secondary_focus,
        'intensity': 'high' if means[primary_focus] > means.mean() else 'moderate'
    }
