import csv
import sys

class ShoppingPoint:
  def load(self, row):
    customer_id, shopping_pt_num, record_type, day, time, state, location, group_size, homeowner, car_age, car_value, risk_factor, age_oldest, age_youngest, married_couple, c_previous, duration_previous, a, b, c, d, e, f, g, cost = row

    self.customer_id = int(customer_id)
    self.shopping_pt_num = int(shopping_pt_num) # 1..x
    self.record_type = int(record_type) # 0 = quote, 1 = buy
    self.day = int(day) # 0..6
    self.time = time # TODO: xx:yy
    self.state = state # TODO: state ID

    if location == 'NA':
      self.location = 0 # TODO
    else:
      self.location = int(location)

    self.group_size = int(group_size)
    self.homeowner = int(homeowner) # 0..1
    self.car_age = int(car_age) # 0..
    self.car_value = car_value # TODO: g/e/c/...?

    if risk_factor == 'NA':
      self.risk_factor = 0 # TODO: lepsi handling N/A
    else:
      self.risk_factor = int(risk_factor)

    self.age_oldest = int(age_oldest)
    self.age_youngest = int(age_youngest)
    self.married_couple = int(married_couple) # 0..1

    if c_previous == 'NA':
      self.c_previous = 0 # TODO: lepsi N/A
    else:
      self.c_previous = int(c_previous) # previous C-value

    if duration_previous == 'NA':
      self.duration_previous = 0
    else:
      self.duration_previous = int(duration_previous)

    if a != 'NA': self.a = int(a)
    if b != 'NA': self.b = int(b)
    if c != 'NA': self.c = int(c)
    if d != 'NA': self.d = int(d)
    if e != 'NA': self.e = int(e)
    if f != 'NA': self.f = int(f)
    if g != 'NA': self.g = int(g)
    self.cost = int(cost)

    self.plan = [self.a, self.b, self.c, self.d, self.e, self.f, self.g]

class Customer:
  def __init__(self, customer_id):
    self.customer_id = customer_id
    self.points = []
    self.selected_plan = None

  def insert_shopping_point(self, point):
    self.points.append(point)

    if point.record_type == 1:
      self.selected_plan = point.plan

  def export_selected_plan(self):
    return ''.join(map(str, self.selected_plan))

  def calculate_derived_data(self):
    self.did_choose_browsed_plan = 0
    for point in self.points:
      if point.record_type == 0 and point.plan == self.selected_plan: # quote
        self.did_choose_browsed_plan = 1

class Data:
  def __init__(self):
    self.customers = {}

  def insert_row(self, row):
    point = ShoppingPoint()
    point.load(row)

    cid = point.customer_id

    if not cid in self.customers:
        self.customers[cid] = Customer(cid)

    self.customers[cid].insert_shopping_point(point)

  def load(self, f):
    reader = csv.reader(f, delimiter=',')

    for row in reader:
      if row[0] == 'customer_ID': # skip
        next
      else:
        self.insert_row(row)

    for customer in self.customers.values():
      customer.calculate_derived_data()

    print("Input loaded.", file=sys.stderr)

  def export_results(self, f):
    writer = csv.writer(f, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['customer_ID', 'plan'])

    for customer in self.customers.values():
      writer.writerow([customer.customer_id, customer.export_selected_plan()])