from app import celery, db
from app.models.user import User
from app.utils.email import send_email
from datetime import datetime, timedelta
import pytz
from app.utils.monitoring import track_resource_usage

@celery.task
@track_resource_usage('send_sabbath_reminders')
def send_sabbath_reminders():
    """Send Sabbath preparation reminders to users"""
    try:
        # Get all active users
        users = User.query.filter_by(active=True, email_verified=True).all()
        
        for user in users:
            try:
                # Get user's timezone
                timezone = pytz.timezone(user.profile.get('timezone', 'UTC'))
                now = datetime.now(timezone)
                
                # Get user's preparation preferences
                prefs = user.profile.get('sabbath_preferences', {})
                prep_start_hour = prefs.get('preparation_start_hour', 14)  # Default 2 PM
                notif_hours = prefs.get('notification_hours_before', 24)
                
                # Calculate next Sabbath
                friday = get_next_friday(now)
                prep_time = friday.replace(hour=prep_start_hour, minute=0)
                
                # Check if it's time to send reminder
                reminder_time = prep_time - timedelta(hours=notif_hours)
                if now >= reminder_time and now < prep_time:
                    send_preparation_reminder.delay(user.id)
            
            except Exception as e:
                celery.logger.error(f"Error processing user {user.id}: {str(e)}")
                continue
        
        return {'status': 'success'}
    except Exception as e:
        celery.logger.error(f"Error sending Sabbath reminders: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@celery.task
def send_preparation_reminder(user_id):
    """Send personalized Sabbath preparation reminder"""
    try:
        user = User.query.get(user_id)
        if not user:
            return {'status': 'error', 'message': 'User not found'}
        
        # Get user's preparation checklist
        checklist = generate_preparation_checklist(user)
        
        # Send email
        subject = "🕊️ Time to Prepare for Sabbath"
        template = 'email/sabbath_reminder.html'
        send_email(
            subject=subject,
            recipients=[user.email],
            template=template,
            user=user,
            checklist=checklist
        )
        
        return {'status': 'success'}
    except Exception as e:
        celery.logger.error(f"Error sending preparation reminder: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@celery.task
def send_spiritual_insights():
    """Send weekly spiritual insights to users"""
    try:
        users = User.query.filter_by(active=True, email_verified=True).all()
        
        for user in users:
            try:
                # Check if user has recent activity
                recent_records = SpiritualRecord.query.filter(
                    SpiritualRecord.user_id == user.id,
                    SpiritualRecord.date >= datetime.utcnow() - timedelta(days=7)
                ).all()
                
                if recent_records:
                    # Generate insights
                    insights = generate_spiritual_insights(user, recent_records)
                    
                    # Send email
                    subject = "📈 Your Weekly Spiritual Journey Update"
                    template = 'email/spiritual_insights.html'
                    send_email(
                        subject=subject,
                        recipients=[user.email],
                        template=template,
                        user=user,
                        insights=insights
                    )
            except Exception as e:
                celery.logger.error(f"Error processing insights for user {user.id}: {str(e)}")
                continue
        
        return {'status': 'success'}
    except Exception as e:
        celery.logger.error(f"Error sending spiritual insights: {str(e)}")
        return {'status': 'error', 'message': str(e)}

def get_next_friday(now):
    """Get next Friday date"""
    days_ahead = 4 - now.weekday()  # Friday is 4
    if days_ahead <= 0:
        days_ahead += 7
    return now + timedelta(days=days_ahead)

def generate_preparation_checklist(user):
    """Generate personalized Sabbath preparation checklist"""
    checklist = {
        'spiritual': [
            'Personal prayer and meditation time',
            'Bible study completion',
            'Family worship preparation'
        ],
        'physical': [
            'House cleaning',
            'Meal preparation',
            'Personal grooming'
        ],
        'service': [
            'Check on church responsibilities',
            'Prepare offerings',
            'Contact prayer partners'
        ]
    }
    
    # Add user-specific items
    if 'custom_prep_items' in user.profile:
        for category, items in user.profile['custom_prep_items'].items():
            if category in checklist:
                checklist[category].extend(items)
    
    return checklist

def generate_spiritual_insights(user, records):
    """Generate personalized spiritual insights"""
    insights = {
        'summary': analyze_weekly_summary(records),
        'achievements': identify_achievements(records, user.profile),
        'suggestions': generate_growth_suggestions(records, user.profile),
        'bible_study': analyze_bible_study_pattern(records),
        'prayer_life': analyze_prayer_pattern(records)
    }
    
    return insights
