# backend/api/main.py

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from db.models import db, Word, Group, WordGroup, StudyActivity, StudySession, WordReviewItem

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///words.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Helper function to paginate results
def paginate(query, page=1, per_page=100, sort_by=None, order='asc'):
    if sort_by:
        if order == 'asc':
            query = query.order_by(getattr(query.model, sort_by).asc())
        else:
            query = query.order_by(getattr(query.model, sort_by).desc())
    return query.paginate(page, per_page, error_out=False)

# Routes

@app.route('/api/words', methods=['GET'])
def get_words():
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', 'kanji', type=str)
    order = request.args.get('order', 'asc', type=str)
    query = Word.query
    pagination = paginate(query, page, sort_by=sort_by, order=order)
    return jsonify({
        'items': [word.to_dict() for word in pagination.items],
        'pagination': {
            'current_page': pagination.page,
            'total_pages': pagination.pages,
            'total_items': pagination.total,
            'items_per_page': pagination.per_page
        }
    })

@app.route('/api/groups', methods=['GET'])
def get_groups():
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', 'name', type=str)
    order = request.args.get('order', 'asc', type=str)
    query = Group.query
    pagination = paginate(query, page, sort_by=sort_by, order=order)
    return jsonify({
        'items': [group.to_dict() for group in pagination.items],
        'pagination': {
            'current_page': pagination.page,
            'total_pages': pagination.pages,
            'total_items': pagination.total,
            'items_per_page': pagination.per_page
        }
    })

@app.route('/api/groups/<int:id>', methods=['GET'])
def get_group(id):
    group = Group.query.get_or_404(id)
    return jsonify(group.to_dict())

@app.route('/api/study_sessions', methods=['POST'])
def create_study_session():
    data = request.json
    group_id = data.get('group_id')
    study_activity_id = data.get('study_activity_id')
    if not group_id or not study_activity_id:
        return jsonify({'error': 'group_id and study_activity_id are required'}), 400
    session = StudySession(group_id=group_id, study_activity_id=study_activity_id)
    db.session.add(session)
    db.session.commit()
    return jsonify(session.to_dict()), 201

@app.route('/api/study_sessions/<int:id>/review', methods=['POST'])
def log_review(id):
    data = request.json
    word_id = data.get('word_id')
    correct = data.get('correct')
    if not word_id or correct is None:
        return jsonify({'error': 'word_id and correct are required'}), 400
    session = StudySession.query.get_or_404(id)
    review = WordReviewItem(word_id=word_id, study_session_id=session.id, correct=correct)
    db.session.add(review)
    db.session.commit()
    return jsonify(review.to_dict()), 201

if __name__ == '__main__':
    app.run(debug=True)