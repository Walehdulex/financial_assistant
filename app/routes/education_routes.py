from flask import Blueprint, render_template, request, jsonify

bp = Blueprint('education', __name__)

#Dictionary of available guides in my model with metadata
GUIDES = {

    'stocks': {'title': 'Stocks Basics', 'level': 'Beginner'},
    'diversification': {'title': 'Portfolio Diversification', 'level': 'Beginner'},
    'risk-management': {'title': 'Risk Management', 'level': 'Intermediate'},
    'technical-analysis': {'title': 'Technical Analysis', 'level': 'Intermediate'},
    'fundamental-analysis': {'title': 'Fundamental Analysis', 'level': 'Intermediate'},
    'investing-basics': {'title': 'Investing Basics', 'level': 'Beginner'},
    'portfolio-theory': {'title': 'Portfolio Theory', 'level': 'Advanced'},
    'market-indicators': {'title': 'Market Indicators', 'level': 'Intermediate'},
    'tax-strategies': {'title': 'Tax-Efficient Investing', 'level': 'Intermediate'}
}

@bp.route('/')
def resources():
    return render_template('education/resources.html', guides=GUIDES)

@bp.route('/glossary')
def glossary():
    terms = {}
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        terms[letter] = []

    return render_template('education/glossary.html', terms=terms)

@bp.route('/guides/<topic>')
def guide(topic):
    if topic not in GUIDES:
        # Handling case where guide doesn't exist
        return render_template('education/guide_not_found.html', topic=topic, guides=GUIDES)

    guide_info = GUIDES[topic]
    return render_template(f'education/guides/{topic}.html', guide_info=guide_info)


@bp.route('/api/guides')
def api_guides():
    """API endpoint to get available guides, with optional filtering"""
    level = request.args.get('level')

    if level:
        filtered_guides = {k: v for k, v in GUIDES.items() if v['level'].lower() == level.lower()}
        return jsonify(filtered_guides)

    return jsonify(GUIDES)