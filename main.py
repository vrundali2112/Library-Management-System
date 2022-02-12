from datetime import date, timedelta

import requests
from flask import Flask, render_template, flash, Markup, session, redirect, request, url_for
from flask_sqlalchemy import SQLAlchemy
import json

import os

from sqlalchemy import ForeignKey, desc

SECRET_KEY = os.urandom(32)

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_server = True

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ******************************************************* BOOKS *****************************************************-->

class Books(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(), nullable=False)
    isbn = db.Column(db.String(), nullable=False)
    author = db.Column(db.String(), nullable=False)
    stock = db.Column(db.Integer(), nullable=False)
    borrow_stock = db.Column(db.Integer(), default=0)
    returned = db.Column(db.Boolean(), default=False)



    def __init__(self, title, isbn, author, stock):
        self.title = title
        self.isbn = isbn
        self.author = author
        self.stock = stock


@app.route('/')
def home_page():
    return render_template('home.html')


@app.route('/books', methods=['GET'])
def book_list():
    books = Books.query.filter_by().all()

    return render_template('books/books.html', params=params, books=books)


@app.route('/insert', methods=['POST'])
def insert():
    if request.method == 'POST':
        title = request.form['title']
        isbn = request.form['isbn']
        author = request.form['author']
        stock = request.form['stock']


        my_data = Books(title, isbn, author, stock)
        db.session.add(my_data)
        db.session.commit()

        flash("Book Inserted successfully")

        return redirect(url_for('book_list'))


@app.route('/update', methods=['GET', 'POST'])
def update():
    if request.method == 'POST':
        my_data = Books.query.get(request.form.get('id'))
        my_data.title = request.form['title']
        my_data.isbn = request.form['isbn']
        my_data.author = request.form['author']
        my_data.stock = request.form['stock']


        db.session.commit()

        flash("Book Updated Successfully!")

        return redirect(url_for('book_list'))


@app.route('/delete/<id>', methods=['GET', 'POST'])
def delete(id):
    my_data = Books.query.get(id)
    db.session.delete(my_data)
    db.session.commit()
    flash("Book Deleted Successfully")

    return redirect(url_for('book_list'))


@app.route('/searchbook')
def SearchBooks():
    return render_template("search_page.html")


@app.route("/display", methods=["POST"])
def display():
    styp = request.form.get("sType")
    skw = request.form.get("KeyWord")
    look_for = '%{0}%'.format(skw)

    if styp == "T":
        lBook = db.session.query(Books).filter(Books.title.ilike(look_for))

    if styp == "A":
        lBook = db.session.query(Books).filter(Books.author.ilike(look_for))

    return render_template('display.html', books=lBook)


@app.route('/import-from-frappe', methods=['GET', 'POST'])
def import_books_from_frappe():
    title = request.form.get('title')
    books = []
    url = f"https://frappe.io/api/method/frappe-library?page=2&title=and"
    books = requests.get(url).json()['message']
    books_list = db.session.query(Books.title).all()
    books_list = list(map(' '.join, books_list))
    author_list = db.session.query(Books.author).all()
    author_list = list(map(' '.join, author_list))
    # if books are succesfully imported
    if len(books) > 0:
        for book in books:
            # if no duplicate book is found
            if book['title'] not in books_list and book['authors'] not in author_list:
                book_to_create = Books(title=book['title'],
                                       isbn=(book['isbn']),
                                       author=book['authors'],
                                       stock=20)
                db.session.add(book_to_create)
                db.session.commit()
            # skips when a duplicate is found
            else:
                continue
        flash("Succesfully Imported", category="success")
    # if error in importing the books
    else:
        flash("No response from the API", category="danger")

    return redirect(url_for('book_list'))


# ******************************************************* MEMBERS *************************************************-->

class Members(db.Model):
    __tablename__='members'
    mid = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), nullable=False)
    member_name = db.Column(db.String(), nullable=False, unique=True)
    phone_num = db.Column(db.String(), nullable=False, unique=True)
    total_paid = db.Column(db.Integer(), default=0)


    def __init__(self, name, member_name, phone_num, total_paid):
        self.name = name
        self.member_name = member_name
        self.phone_num = phone_num
        self.total_paid = total_paid


@app.route('/members', methods=['GET'])
def member_list():
    members = Members.query.filter_by().all()
    return render_template('members/members.html', params=params, members=members)


@app.route('/insert_mem', methods=['GET', 'POST'])
def insert_mem():
    if request.method == 'POST':
        name = request.form['name']
        member_name = request.form['member_name']
        phone_num = request.form['phone_num']
        total_paid = request.form.get('total_paid', False)

        my_data1 = Members(name, member_name, phone_num, total_paid)
        db.session.add(my_data1)
        db.session.commit()

        flash("Member Inserted successfully")

        return redirect(url_for('member_list'))


@app.route('/update_mem', methods=['GET', 'POST'])
def update_mem():
    if request.method == 'POST':
        my_data = Members.query.get(request.form.get('mid'))
        my_data.name = request.form['name']
        my_data.member_name = request.form['member_name']
        my_data.phone_num = request.form['phone_num']
        my_data.total_paid = request.form['total_paid']

        db.session.commit()

        flash("Member Updated Successfully")

        return redirect(url_for('member_list'))


@app.route('/delete_mem/<mid>', methods=['GET', 'POST'])
def delete_mem(mid):
    my_data = Members.query.get(mid)
    db.session.delete(my_data)
    db.session.commit()
    flash("Member Removed Successfully")

    return redirect(url_for('member_list'))

@app.route('/searchmem', methods=['GET','POST'])
def SearchMem():
    q = request.form.get("q")
    look_for = '%{0}%'.format(q)
    lMember = db.session.query(Members).filter(Members.member_name.ilike(look_for))

    return render_template('members/search_mem.html', datas=lMember)



# ***************************Issue a Book ******************8-->
class Issuereturn(db.Model):
    __tablename__ = 'issuereturn'
    transID = db.Column(db.Integer, primary_key=True)
    booktitle = db.Column(db.String, nullable=False)
    membername = db.Column(db.String, nullable=False)
    IssueDate = db.Column(db.Date, nullable=False)
    ExpRetDate = db.Column(db.Date, nullable=False)
    ActRetDate = db.Column(db.Date, nullable=False)
    OverdueDays = db.Column(db.Integer, nullable=False, default=0)


    def __init__(self, booktitle, membername, IssueDate, ExpRetDate, ActRetDate, OverdueDays):
        self.booktitle = booktitle
        self.membername = membername
        self.IssueDate = IssueDate
        self.ExpRetDate = ExpRetDate
        self.ActRetDate = ActRetDate
        self.OverdueDays = OverdueDays





@app.route('/transactions')
def transaction_list():
    datas = Issuereturn.query.filter_by().all()
    return render_template("transactions/transactions.html", params=params, datas=datas)


@app.route('/issuebook', methods=['GET', 'POST'])
def issuebook():
    if request.method == 'POST':
        booktitle = request.form.get('booktitle')
        membername = request.form.get('membername')
        IssueDate = date.today()
        ExpRetDate = date.today() + timedelta(days=14)
        ActRetDate = date.today()
        OverdueDays = 0
        books = Books.query.get(booktitle)

        my_data = Issuereturn(booktitle, membername, IssueDate, ExpRetDate, ActRetDate, OverdueDays)

        db.session.add(my_data)

        db.session.commit()

        flash("Book Issued Successfully, Please update the stock Column in Book List!")

        return redirect(url_for('transaction_list'))


@app.route('/update_ret', methods=['GET', 'POST'])
def update_ret():
    if request.method == 'POST':
        dta = Issuereturn.query.get(request.form.get('transID'))
        dta.membername = request.form['membername']
        dta.ActRetDate = request.form['ActRetDate']
        dta.OverdueDays = request.form['OverdueDays']


        db.session.commit()

        flash("Status Updated Successfully")

        return redirect(url_for('transaction_list'))


@app.route("/display_members", methods=["POST"])
def display_members():
    utyp = request.form.get("uType")
    skw = request.form.get("KeyWord")
    look_for = '%{0}%'.format(skw)

    if utyp == "B":
        lBook = db.session.query(Issuereturn).filter(Issuereturn.booktitle.ilike(look_for))

    if utyp == "U":
        lBook = db.session.query(Issuereturn).filter(Issuereturn.membername.ilike(look_for))

    return render_template('transactions/display_members.html', books=lBook)


@app.route('/searchret', methods=['GET','POST'])
def SearchRet():
    q = request.form.get("q")
    look_for = '%{0}%'.format(q)
    lBook = db.session.query(Issuereturn).filter(Issuereturn.membername.ilike(look_for))

    return render_template('transactions/search_ret.html', datas=lBook)

@app.route("/aboutsystem")
def aboutsystem():
    return render_template('aboutsystem.html')




app.run(debug=True)
