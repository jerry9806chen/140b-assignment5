from wsgiref.simple_server import make_server
from pyramid.config import Configurator

from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound

from pyramid.response import Response
from pyramid.response import FileResponse

from pyramid.session import SignedCookieSessionFactory

import mysql.connector as mysql
import json
import requests

import os

# For timestamps
from datetime import datetime

db_user = os.environ['MYSQL_USER']
db_pass = os.environ['MYSQL_PASSWORD']
db_name = os.environ['MYSQL_DATABASE']
db_host = os.environ['MYSQL_HOST']

about = '/about'
admin = '/admin'
home = '/home'
login = '/login'
product = '/product'
pricing = '/pricing'
register = '/register'

#--- the server starts up on the home page.
def server_start(req):
  return HTTPFound(req.route_url("get_home"))

#--- this route will show the about us page.
def get_about(req):
  route_name = about
  if 'user' in req.session: # logged in
    record_visit(req.session['user'], route_name)
    return render_to_response("templates/about.html", {'user':req.session['user']}, request=req)
  # not logged in
  record_visit('NONE', route_name)
  return render_to_response("templates/about.html", {}, request=req)

#___ this route will retrieve the admin page if the user is logged in.
#___ Otherwise there will be a redirect to the login page.
def get_admin(req):
  route_name = admin
  if 'user' in req.session: # logged in
    record_visit(req.session['user'], route_name)
    return render_to_response('templates/admin.html',{'user':req.session['user'],'visits':fetch_admindata()})
  else: # not logged in
    return HTTPFound(req.route_url("get_login"))

#--- this route will show the home page.
def get_home(req):
  route_name = home
  if 'user' in req.session: # logged in
    record_visit(req.session['user'], route_name)
    return render_to_response("templates/home.html", {'user':req.session['user']}, request=req)
  # not logged in
  record_visit('NONE', route_name)
  return render_to_response("templates/home.html", {}, request=req)

# -- this route will show the login page.
# -- if a user is logged in, the route will redirect to the admin page instead.
def get_login(req):
  route_name = login
  error = req.session.pop_flash('login_error')
  error = error[0] if error else ''
  if 'user' in req.session:
    return HTTPFound(req.route_url("get_admin"))
  record_visit('NONE', route_name)
  return render_to_response('templates/login.html', {'error': error})

#--- this route will show the registration page.
# -- if a user is logged in, the route will redirect to the admin page instead.
def get_register(req):
  route_name = register
  if 'user' in req.session:
    return HTTPFound(req.route_url("get_admin"))
  record_visit('NONE', route_name)
  return render_to_response('templates/register.html', {})

#___ this route will show the pricing page.
def get_price(req):
  route_name = pricing
  if 'user' in req.session: # logged in
    record_visit(req.session['user'], route_name)
    return render_to_response("templates/pricing.html", {'user':req.session['user']}, request=req)
  # not logged in
  record_visit('NONE', route_name)
  return render_to_response("templates/pricing.html", {}, request=req)

#___ this route will show the product features page
def get_prod(req):
  route_name = product
  if 'user' in req.session: # logged in
    record_visit(req.session['user'], route_name)
    return render_to_response("templates/product.html", {'user':req.session['user']}, request=req)
  # not logged in
  record_visit('NONE', route_name)
  return render_to_response("templates/product.html", {}, request=req)

# Route to handle login form submissions coming from the login page
def post_login(req):
  email = None
  password = None
  if req.method == "POST":
    email = req.params['email']
    password = req.params['password']

  # Connect to the database and try to retrieve the user
  db = mysql.connect(host=db_host, database=db_name, user=db_user, passwd=db_pass)
  cursor = db.cursor()
  query = "SELECT email, password FROM Users WHERE email='%s';" % email
  cursor.execute(query)
  user = cursor.fetchone() # will return a tuple (email, password) if user is found and None otherwise
  db.close()

  # If user is found and the password is valid, store in session, and redirect to the homepage
  # Otherwise, redirect back to the login page with a flash message
  # Note: passwords should be hashed and encrypted in actual production solutions!
  if user is not None and user[1] == password:
    req.session['user'] = user[0] # set the session variable
    return HTTPFound(req.route_url("get_admin"))
  else:
    req.session.invalidate() # clear session
    req.session.flash('Invalid login attempt. Please try again.', 'login_error')
    return HTTPFound(req.route_url("get_login"))

def post_register(req):
  first_name = req.POST['first_name']
  last_name = req.POST['last_name']
  email = req.POST['email']
  password = req.POST['password']

  save_user_details(first_name, last_name, email, password)

  return HTTPFound(req.route_url("get_admin"))

def save_user_details(first_name, last_name, email, password):
  db = mysql.connect(host=db_host, database=db_name, user=db_user, passwd=db_pass)
  cursor = db.cursor()
  query = "insert into Users (first_name, last_name, email, password, created_at) values (%s, %s, %s, %s, %s)"
  values = [
    (first_name, last_name, email, password, datetime.now())
  ]
  cursor.executemany(query, values)
  db.commit()
  db.close()

def record_visit(user_id, route_name):
  db = mysql.connect(host=db_host, database=db_name, user=db_user, passwd=db_pass)
  cursor = db.cursor()
  query = "insert into Visits (session_id, route_name, timestamp) values (%s, %s, %s)"
  values = [
    (user_id, route_name, datetime.now())
  ]
  cursor.executemany(query, values)
  db.commit()

  visit_count = {}
  visit_count[about] = 0
  visit_count[admin] = 0
  visit_count[home] = 0
  visit_count[login] = 0
  visit_count[pricing] = 0
  visit_count[product] = 0
  visit_count[register] = 0
  cursor.execute("select * from Visits;")
  for row in cursor:
    visit_count[row[2]] += 1

  cursor = db.cursor()
  cursor.execute("drop table if exists Visit_Count;")
  try:
    cursor.execute("""
      CREATE TABLE Visit_Count (
      id          integer AUTO_INCREMENT PRIMARY KEY,
      route_name  VARCHAR(30) NOT NULL,
      visit_count VARCHAR(30) NOT NULL
      );
    """)
    db.commit()
  except:
    print("Visit_Count Table already exists. Not recreating it.")

  cursor = db.cursor()
  query = "insert into Visit_Count (route_name, visit_count) values (%s, %s)"
  values = []
  for count in visit_count:
    values += [(count, str(visit_count[count]))]

  cursor.executemany(query, values)
  db.commit()

  db.close()

def fetch_admindata():
  db = mysql.connect(host=db_host, database=db_name, user=db_user, passwd=db_pass)
  cursor = db.cursor()
  cursor.execute("select * from Visit_Count;")
  visit_count = []
  for row in cursor:
    visit_count += [[row[1], row[2]]]
  return visit_count

def logout(req):
  if 'user' in req.session: # logged in
    #del req.session['user']
    req.session.invalidate() # clear session
    return render_to_response("templates/home.html", {}, request=req)
  else:
    return render_to_response('templates/home.html', {'error': 'Logout Error'})

if __name__ == '__main__':
  config = Configurator()

  # Templating renderer
  config.include('pyramid_jinja2')
  config.add_jinja2_renderer('.html')

  config.add_route('start', '/')
  config.add_view(server_start, route_name='start')

  config.add_route('get_about', '/about')
  config.add_view(get_about, route_name='get_about')

  config.add_route('get_admin', '/admin')
  config.add_view(get_admin, route_name='get_admin')

  config.add_route('get_home', '/home')
  config.add_view(get_home, route_name='get_home')

  config.add_route('get_login', '/login')
  config.add_view(get_login, route_name='get_login')

  config.add_route('post_login', '/post_login')
  config.add_view(post_login, route_name='post_login')

  config.add_route('get_register', '/register')
  config.add_view(get_register, route_name='get_register')

  config.add_route('post_register', '/post_register')
  config.add_view(post_register, route_name='post_register')

  config.add_route('get_pricing', '/pricing')
  config.add_view(get_price, route_name='get_pricing')

  config.add_route('product', '/product')
  config.add_view(get_prod, route_name='product')

  config.add_route('logout', '/logout')
  config.add_view(logout, route_name='logout')
  
  # Path for static resources
  config.add_static_view(name='/', path='./public', cache_max_age=3600)

  # Create the session using a signed
  session_factory = SignedCookieSessionFactory(os.environ['SESSION_SECRET_KEY'])
  config.set_session_factory(session_factory)

  # Start the server on port 6000 (arbitrarily chosen)
  app = config.make_wsgi_app()
  server = make_server('0.0.0.0', 6000, app)
  server.serve_forever()
