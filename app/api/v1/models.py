from flask_restx import Model, fields

# Auth Models
login_model = Model('Login', {
    'username': fields.String(required=True, description='Username'),
    'password': fields.String(required=True, description='Password')
})

register_model = Model('Register', {
    'username': fields.String(required=True, description='Username'),
    'email': fields.String(required=True, description='Email address'),
    'password': fields.String(required=True, description='Password'),
    'timezone': fields.String(description='User timezone', default='UTC')
})

user_profile = Model('UserProfile', {
    'sabbath_preferences': fields.Raw(description='Sabbath preparation preferences'),
    'spiritual_goals': fields.Raw(description='Spiritual growth goals'),
    'doctrinal_interests': fields.List(fields.String, description='Areas of doctrinal interest'),
    'ministry_involvement': fields.List(fields.String, description='Ministry involvement areas')
})

user_model = Model('User', {
    'id': fields.Integer(description='User ID'),
    'username': fields.String(description='Username'),
    'email': fields.String(description='Email address'),
    'email_verified': fields.Boolean(description='Email verification status'),
    'active': fields.Boolean(description='Account status'),
    'created_at': fields.DateTime(description='Account creation timestamp'),
    'last_seen': fields.DateTime(description='Last activity timestamp'),
    'profile': fields.Nested(user_profile, description='User profile data')
})

# Spiritual Models
spiritual_record = Model('SpiritualRecord', {
    'id': fields.Integer(description='Record ID'),
    'date': fields.Date(description='Record date'),
    'category': fields.String(description='Record category'),
    'metrics': fields.Raw(description='Record metrics'),
    'notes': fields.String(description='Additional notes')
})

prayer_request = Model('PrayerRequest', {
    'id': fields.Integer(description='Prayer request ID'),
    'title': fields.String(required=True, description='Prayer request title'),
    'request': fields.String(required=True, description='Prayer request content'),
    'is_answered': fields.Boolean(description='Prayer answer status'),
    'answer_notes': fields.String(description='Notes about prayer answer'),
    'is_private': fields.Boolean(description='Privacy setting'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'answered_at': fields.DateTime(description='Answer timestamp')
})

bible_study = Model('BibleStudy', {
    'id': fields.Integer(description='Study session ID'),
    'date': fields.Date(description='Study date'),
    'book': fields.String(required=True, description='Bible book'),
    'chapter': fields.Integer(required=True, description='Chapter number'),
    'verses': fields.String(description='Specific verses studied'),
    'notes': fields.String(description='Study notes'),
    'duration_minutes': fields.Integer(required=True, description='Study duration')
})

# Sabbath Models
sabbath_times = Model('SabbathTimes', {
    'start': fields.DateTime(description='Sabbath start time'),
    'end': fields.DateTime(description='Sabbath end time'),
    'candle_lighting': fields.DateTime(description='Candle lighting time'),
    'havdalah': fields.DateTime(description='Havdalah time'),
    'timezone': fields.String(description='Local timezone'),
    'location': fields.Raw(description='Location details')
})

preparation_checklist = Model('PreparationChecklist', {
    'spiritual': fields.List(fields.String, description='Spiritual preparation tasks'),
    'physical': fields.List(fields.String, description='Physical preparation tasks'),
    'service': fields.List(fields.String, description='Service-related tasks'),
    'custom': fields.List(fields.String, description='User-defined tasks')
})

# Response Models
success_response = Model('Success', {
    'message': fields.String(description='Success message'),
    'data': fields.Raw(description='Response data')
})

error_response = Model('Error', {
    'error': fields.String(description='Error message'),
    'code': fields.Integer(description='Error code'),
    'details': fields.Raw(description='Error details')
})

pagination = Model('Pagination', {
    'page': fields.Integer(description='Current page number'),
    'per_page': fields.Integer(description='Items per page'),
    'total': fields.Integer(description='Total number of items'),
    'pages': fields.Integer(description='Total number of pages')
})
