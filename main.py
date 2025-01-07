from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import case
import os

# Create the Flask application
app = Flask(__name__)

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create the SQLAlchemy object
db = SQLAlchemy()
# Initialize the app with the extension
db.init_app(app)

def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database recreated successfully!")

class Todo(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    priority = db.Column(db.String(20), default='low')
    category = db.Column(db.String(20), default='other')
    due_date = db.Column(db.Date, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"{self.sno} - {self.title}"

@app.route('/', methods=['GET', 'POST'])
def hello_world():
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['desc']
        priority = request.form.get('priority', 'low')
        category = request.form.get('category', 'other')
        due_date_str = request.form.get('due_date')
        
        if title and desc:
            todo = Todo(
                title=title,
                desc=desc,
                priority=priority,
                category=category,
                due_date=datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
            )
            db.session.add(todo)
            db.session.commit()
        else:
            return render_template('index.html', allTodo=Todo.query.all(), error="Please fill both title and description!")
    
    # Handle sorting
    sort = request.args.get('sort', 'date')
    if sort == 'priority':
        todos = Todo.query.order_by(
            case(
                (Todo.priority == 'high', 1),
                (Todo.priority == 'medium', 2),
                else_=3
            )
        ).all()
    elif sort == 'title':
        todos = Todo.query.order_by(Todo.title).all()
    else:  # default sort by date
        todos = Todo.query.order_by(Todo.date_created.desc()).all()
    
    return render_template('index.html', allTodo=todos)

@app.route('/show')
def products():
    allTodo = Todo.query.all()
    print(allTodo)
    return render_template('index.html', allTodo=allTodo)

@app.route('/update/<int:sno>', methods=['GET', 'POST'])
def update(sno):
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['desc']
        todo = Todo.query.filter_by(sno=sno).first()
        todo.title = title
        todo.desc = desc
        db.session.add(todo)
        db.session.commit()
        return redirect('/')
    todo = Todo.query.filter_by(sno=sno).first()
    return render_template('update.html', todo=todo)

@app.route('/delete/<int:sno>')
def delete(sno):
    todo = Todo.query.filter_by(sno=sno).first()
    db.session.delete(todo)
    db.session.commit()
    return redirect('/')

@app.route('/search')
def search():
    query = request.args.get('query', '')
    if query:
        # Search in both title and description
        search_results = Todo.query.filter(
            (Todo.title.contains(query)) | 
            (Todo.desc.contains(query))
        ).all()
    else:
        search_results = []
    return render_template('index.html', allTodo=search_results)

@app.route('/about')
def about():
    total_todos = Todo.query.count()
    completed_todos = 0  # You'll need to add a 'completed' field to implement this
    latest_todo = Todo.query.order_by(Todo.date_created.desc()).first()
    stats = {
        'total_todos': total_todos,
        'active_todos': total_todos,
        'latest_todo': latest_todo,
        'app_started': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return render_template('about.html', stats=stats)

@app.route('/toggle/<int:sno>')
def toggle_complete(sno):
    todo = Todo.query.filter_by(sno=sno).first()
    if todo:
        todo.completed = not todo.completed
        db.session.commit()
        return {'success': True}
    return {'success': False}

if __name__ == "__main__":
    init_db()  # Initialize database before running app
    app.run(debug=True, port=8000)
