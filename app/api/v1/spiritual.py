from flask_restx import Namespace, Resource
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User, SpiritualRecord, PrayerRequest, BibleStudy
from app import db, limiter
from app.utils.monitoring import track_resource_usage
from datetime import datetime, timedelta
from sqlalchemy import func
from .models import (
    spiritual_record, prayer_request, bible_study,
    success_response, error_response, pagination
)

spiritual_ns = Namespace(
    'spiritual',
    description='Spiritual growth tracking and analysis',
    decorators=[jwt_required()]
)

# Register models
spiritual_ns.models[spiritual_record.name] = spiritual_record
spiritual_ns.models[prayer_request.name] = prayer_request
spiritual_ns.models[bible_study.name] = bible_study
spiritual_ns.models[success_response.name] = success_response
spiritual_ns.models[error_response.name] = error_response
spiritual_ns.models[pagination.name] = pagination

@spiritual_ns.route('/record')
class SpiritualRecordResource(Resource):
    @spiritual_ns.doc('create_record')
    @spiritual_ns.expect(spiritual_record)
    @spiritual_ns.response(201, 'Record created', success_response)
    @spiritual_ns.response(400, 'Validation error', error_response)
    @track_resource_usage('create_spiritual_record')
    def post(self):
        """Create a new spiritual growth record"""
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate input
        validation = validate_spiritual_record(data)
        if validation is not True:
            return jsonify({'error': validation}), 400
        
        try:
            record = SpiritualRecord(
                user_id=current_user_id,
                category=data['category'],
                metrics=data['metrics'],
                notes=data.get('notes', '')
            )
            
            db.session.add(record)
            db.session.commit()
            
            return jsonify({
                'message': 'Record created successfully',
                'id': record.id
            }), 201
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Record creation error: {str(e)}")
            return jsonify({'error': 'Failed to create record'}), 500

@spiritual_ns.route('/records')
class SpiritualRecordList(Resource):
    @spiritual_ns.doc('get_records')
    @spiritual_ns.param('category', 'Filter by category')
    @spiritual_ns.param('start_date', 'Start date (YYYY-MM-DD)')
    @spiritual_ns.param('end_date', 'End date (YYYY-MM-DD)')
    @spiritual_ns.param('page', 'Page number', type=int)
    @spiritual_ns.param('per_page', 'Items per page', type=int)
    @spiritual_ns.response(200, 'Success', model=spiritual_record)
    @track_resource_usage('get_spiritual_records')
    def get(self):
        """Get user's spiritual records with filtering and pagination"""
        current_user_id = get_jwt_identity()
        
        # Parse query parameters
        category = request.args.get('category')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)
        
        # Build query
        query = SpiritualRecord.query.filter_by(user_id=current_user_id)
        
        if category:
            query = query.filter_by(category=category)
        if start_date:
            query = query.filter(SpiritualRecord.date >= start_date)
        if end_date:
            query = query.filter(SpiritualRecord.date <= end_date)
        
        # Execute paginated query
        records = query.order_by(SpiritualRecord.date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'records': [
                {
                    'id': r.id,
                    'date': r.date.isoformat(),
                    'category': r.category,
                    'metrics': r.metrics,
                    'notes': r.notes
                }
                for r in records.items
            ],
            'total': records.total,
            'pages': records.pages,
            'current_page': records.page
        }), 200

@spiritual_ns.route('/prayer-request')
class PrayerRequestResource(Resource):
    @spiritual_ns.doc('create_prayer_request')
    @spiritual_ns.expect(prayer_request)
    @spiritual_ns.response(201, 'Prayer request created', success_response)
    @track_resource_usage('create_prayer_request')
    def post(self):
        """Create a new prayer request"""
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not all(k in data for k in ('title', 'request')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        try:
            prayer_request = PrayerRequest(
                user_id=current_user_id,
                title=data['title'],
                request=data['request'],
                is_private=data.get('is_private', True)
            )
            
            db.session.add(prayer_request)
            db.session.commit()
            
            return jsonify({
                'message': 'Prayer request created successfully',
                'id': prayer_request.id
            }), 201
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Prayer request creation error: {str(e)}")
            return jsonify({'error': 'Failed to create prayer request'}), 500

@spiritual_ns.route('/prayer-requests')
class PrayerRequestList(Resource):
    @spiritual_ns.doc('get_prayer_requests')
    @spiritual_ns.param('status', 'Filter by status (answered, unanswered, all)')
    @spiritual_ns.param('page', 'Page number', type=int)
    @spiritual_ns.param('per_page', 'Items per page', type=int)
    @spiritual_ns.response(200, 'Success', model=prayer_request)
    @track_resource_usage('get_prayer_requests')
    def get(self):
        """Get user's prayer requests"""
        current_user_id = get_jwt_identity()
        
        # Parse query parameters
        status = request.args.get('status')  # answered, unanswered, all
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)
        
        # Build query
        query = PrayerRequest.query.filter_by(user_id=current_user_id)
        
        if status == 'answered':
            query = query.filter_by(is_answered=True)
        elif status == 'unanswered':
            query = query.filter_by(is_answered=False)
        
        # Execute paginated query
        requests = query.order_by(PrayerRequest.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'prayer_requests': [
                {
                    'id': r.id,
                    'title': r.title,
                    'request': r.request,
                    'is_answered': r.is_answered,
                    'answer_notes': r.answer_notes,
                    'created_at': r.created_at.isoformat(),
                    'answered_at': r.answered_at.isoformat() if r.answered_at else None
                }
                for r in requests.items
            ],
            'total': requests.total,
            'pages': requests.pages,
            'current_page': requests.page
        }), 200

@spiritual_ns.route('/bible-study')
class BibleStudyResource(Resource):
    @spiritual_ns.doc('create_bible_study')
    @spiritual_ns.expect(bible_study)
    @spiritual_ns.response(201, 'Bible study recorded', success_response)
    @track_resource_usage('create_bible_study')
    def post(self):
        """Record a Bible study session"""
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ('book', 'chapter', 'duration_minutes')
        if not all(k in data for k in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        try:
            study = BibleStudy(
                user_id=current_user_id,
                book=data['book'],
                chapter=data['chapter'],
                verses=data.get('verses'),
                notes=data.get('notes'),
                duration_minutes=data['duration_minutes']
            )
            
            db.session.add(study)
            db.session.commit()
            
            return jsonify({
                'message': 'Bible study recorded successfully',
                'id': study.id
            }), 201
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Bible study creation error: {str(e)}")
            return jsonify({'error': 'Failed to record Bible study'}), 500

@spiritual_ns.route('/bible-studies')
class BibleStudyList(Resource):
    @spiritual_ns.doc('get_bible_studies')
    @spiritual_ns.param('book', 'Filter by Bible book')
    @spiritual_ns.param('start_date', 'Start date (YYYY-MM-DD)')
    @spiritual_ns.param('end_date', 'End date (YYYY-MM-DD)')
    @spiritual_ns.param('page', 'Page number', type=int)
    @spiritual_ns.param('per_page', 'Items per page', type=int)
    @spiritual_ns.response(200, 'Success', model=bible_study)
    @track_resource_usage('get_bible_studies')
    def get(self):
        """Get user's Bible study records"""
        current_user_id = get_jwt_identity()
        
        # Parse query parameters
        book = request.args.get('book')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)
        
        # Build query
        query = BibleStudy.query.filter_by(user_id=current_user_id)
        
        if book:
            query = query.filter_by(book=book)
        if start_date:
            query = query.filter(BibleStudy.date >= start_date)
        if end_date:
            query = query.filter(BibleStudy.date <= end_date)
        
        # Execute paginated query
        studies = query.order_by(BibleStudy.date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'bible_studies': [
                {
                    'id': s.id,
                    'date': s.date.isoformat(),
                    'book': s.book,
                    'chapter': s.chapter,
                    'verses': s.verses,
                    'notes': s.notes,
                    'duration_minutes': s.duration_minutes
                }
                for s in studies.items
            ],
            'total': studies.total,
            'pages': studies.pages,
            'current_page': studies.page
        }), 200

@spiritual_ns.route('/stats')
class SpiritualStats(Resource):
    @spiritual_ns.doc('get_stats')
    @spiritual_ns.param('days', 'Number of days to analyze', type=int)
    @spiritual_ns.response(200, 'Success', success_response)
    @track_resource_usage('get_spiritual_stats')
    def get(self):
        """Get spiritual growth statistics"""
        current_user_id = get_jwt_identity()
        
        # Get date range
        days = request.args.get('days', 30, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        try:
            # Bible study stats
            bible_study_stats = db.session.query(
                func.count(BibleStudy.id).label('total_sessions'),
                func.sum(BibleStudy.duration_minutes).label('total_minutes'),
                func.avg(BibleStudy.duration_minutes).label('avg_duration')
            ).filter(
                BibleStudy.user_id == current_user_id,
                BibleStudy.date >= start_date
            ).first()
            
            # Prayer request stats
            prayer_stats = db.session.query(
                func.count(PrayerRequest.id).label('total_requests'),
                func.sum(case((PrayerRequest.is_answered == True, 1), else_=0)).label('answered_prayers')
            ).filter(
                PrayerRequest.user_id == current_user_id,
                PrayerRequest.created_at >= start_date
            ).first()
            
            # Spiritual record stats by category
            category_stats = {}
            for category in ['bible_study', 'prayer', 'service', 'health']:
                stats = db.session.query(
                    func.count(SpiritualRecord.id).label('total_records')
                ).filter(
                    SpiritualRecord.user_id == current_user_id,
                    SpiritualRecord.category == category,
                    SpiritualRecord.date >= start_date
                ).first()
                category_stats[category] = stats.total_records if stats else 0
            
            return jsonify({
                'bible_study': {
                    'total_sessions': bible_study_stats.total_sessions or 0,
                    'total_minutes': bible_study_stats.total_minutes or 0,
                    'avg_duration': round(bible_study_stats.avg_duration or 0, 2)
                },
                'prayer': {
                    'total_requests': prayer_stats.total_requests or 0,
                    'answered_prayers': prayer_stats.answered_prayers or 0
                },
                'categories': category_stats,
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'days': days
                }
            }), 200
        except Exception as e:
            current_app.logger.error(f"Stats calculation error: {str(e)}")
            return jsonify({'error': 'Failed to calculate statistics'}), 500
