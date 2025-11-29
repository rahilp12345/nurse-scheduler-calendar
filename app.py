import os, sqlite3, json, datetime
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

DB = 'scheduler.db'

def init_db():
    if os.path.exists(DB):
        return
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, title TEXT, start TEXT, end TEXT, allDay INTEGER, type TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS important_dates (id INTEGER PRIMARY KEY, title TEXT, date TEXT, notes TEXT)')

    important = [
        ('Block A Start', '2026-01-04', 'Start of block'),
        ('Block A End', '2026-02-14', 'End of block'),
        ('Education Blackout', '2026-01-18', 'No schedule changes allowed'),
        ('Stat Holiday', '2026-02-02', 'Statutory holiday')
    ]

    for t, d, n in important:
        c.execute('INSERT INTO important_dates (title, date, notes) VALUES (?, ?, ?)', (t, d, n))

    conn.commit()
    conn.close()

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

@app.route('/')
def index():
    return render_template('calendar.html')

@app.route('/api/important_dates')
def get_important():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    rows = c.execute('SELECT id,title,date,notes FROM important_dates').fetchall()
    conn.close()
    data = [{'id':r[0],'title':r[1],'date':r[2],'notes':r[3]} for r in rows]
    return jsonify(data)

@app.route('/api/events')
def get_events():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    rows = c.execute('SELECT id,title,start,end,allDay,type FROM events').fetchall()
    conn.close()
    data = [{'id':r[0],'title':r[1],'start':r[2],'end':r[3],'allDay':bool(r[4]),'type':r[5]} for r in rows]
    return jsonify(data)

@app.route('/api/events', methods=['POST'])
def create_event():
    payload = request.get_json()
    title = payload.get('title','Shift')
    start = payload.get('start')
    end = payload.get('end', start)
    allday = 1 if payload.get('allDay', False) else 0
    etype = payload.get('type','shift')

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('INSERT INTO events (title,start,end,allDay,type) VALUES (?,?,?,?,?)', (title,start,end,allday,etype))
    conn.commit()
    event_id = c.lastrowid
    conn.close()
    return jsonify({'status':'ok','id':event_id})

@app.route('/api/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('DELETE FROM events WHERE id=?', (event_id,))
    conn.commit()
    conn.close()
    return jsonify({'status':'deleted'})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
