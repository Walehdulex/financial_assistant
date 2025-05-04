from app import create_app, db
from app.monitoring.metrics import ResponseMetric

app = create_app()
with app.app_context():
    records = ResponseMetric.query.all()
    print(f"Total records: {len(records)}")

    # Print the most recent 5 records
    for record in ResponseMetric.query.order_by(ResponseMetric.timestamp.desc()).limit(5).all():
        print(f"Route: {record.route}, Time: {record.response_time}, Timestamp: {record.timestamp}")