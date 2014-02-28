# This model selects the most likely of the quoted plans.
# The likelihood is determined by the product of class scores on trained SVMs.


import sys
import fileinput
from sklearn import svm, metrics
from sklearn.externals import joblib
from sklearn.preprocessing import StandardScaler
import multiprocessing

print("Loading input.", file=sys.stderr)

from insurance import Data
dataset = Data()
dataset.load(sys.stdin)

# Napady:
#   - zkusit tomu dat za vstup tu hodnotu parametru, ktera dostala nejmensi cenu.
#   - u kolika zakazniku vubec dochazi k nejakym zmenam?
#   - identifikovat obvykle kombinace.
#   - nejak do toho zahrnout i cenu.
#   - nejak do toho zahrnout bool flagy, jake veci jsem si prohledl.
#   - stane se nekdy, ze si vyberu pojisteni, jehoz nejaky flag jsem si nenechal nikdy naquotovat?

# TODO: vyzkouset:
#   - nejaka ta chytra volba parametru
#   - jeden velky klasifikator?
#   - hodne pravdepodobne si vyberu plan, ktery jsem prohlizel hodnekrat!

# TODO: je dobry napad tomu klasifikatoru davat jako vstup i prvni a posledni
# quote, i kdyz ten klasifikator ma zhodnocovat jejich pravdepodobnost?

# TODO: deterministicke experimenty?

def customer_to_data(customer):
  data = []

  p = customer.points[0]
  data.extend([p.day, p.group_size, p.homeowner, p.car_age, p.car_value, p.risk_factor, p.c_previous, p.age_oldest, p.age_youngest, p.married_couple, p.cost])
  # zajimave... on tomu cost moc nepridava...
  #data.extend([p.a, p.b, p.c, p.d, p.e, p.f, p.g]) #, p.cost])

  # Further attributes:
  #   - time
  #   - state
  #   - location
  #   - duration_previous
  #   - cost

  best, bestc = None, 0
  for p in customer.points:
    n = 0
    for q in customer.points:
      if q.plan == p.plan:
        n += 1
    if n >= bestc:
      best, bestc = p.plan, n

  data.extend(best)
  # data.extend(customer.points[-1].plan) # , p.cost])
  data.append(len(customer.points))

  return data

def classify_customer_plan(customer):
  plan = []
  data = scaler.transform(customer_to_data(customer))

  probs = list(map(lambda i: classifiers[i].predict_proba(data)[0], range(0,7)))

  best, best_score = None, None

  for point in customer.points:
    score = 1.0
    for i in range(0,7):
      score *= probs[i][point.plan[i]]
  #  print("%s: score %f" % (str(point.plan), score), file=sys.stderr)
    if best == None or score > best_score:
      best = list(point.plan)
      best_score = score
  #print(file=sys.stderr)

  # return [1,1,1,1,1,1,1]
  # Select best hypothesis of each classifier:
  ###  for i in range(0,7):
  ###    plan.append(classifiers[i].predict(data)[0]) # 1
  ###
  ###  customer.selected_plan = plan

  print("%d => %s" % (customer.customer_id, str(best)), file=sys.stderr)
  return [customer.customer_id, best]

classifiers = None
scaler = None
# An attempt to automatically find the cases that don't choose what they
# browsed. This doesn't happen a lot, through, so it's dropped for now.
##  # TODO: normalizovat data na 0-1
##  def train_chosen_browsed_plan():
##    print("Training chosen-browsed-plan classifier.")
##    data = list(map(customer_to_data, dataset.customers.values()))
##    target = list(map(lambda c: c.did_choose_browsed_plan, dataset.customers.values()))
##  
##    n = int(len(data) * 0.8)
##  
##    nlc_classifier = svm.SVC(gamma=0.01)
##    nlc_classifier.fit(data[:n], target[:n])
##    predicted = nlc_classifier.predict(data[n:])
##    print("Classifier report for %s:\n%s\n" % (nlc_classifier, metrics.classification_report(target[n:], predicted))) 
##    joblib.dump(nlc_classifier, "trained/nlc_classifier.pkl")

def train_attribute_classifiers():
  print("Training attribute classifiers.")
  data = list(map(customer_to_data, dataset.customers.values()))

  scaler = StandardScaler()
  scaler.fit(data)
  joblib.dump(scaler, "trained/scaler.pkl")
  data = scaler.transform(data)

  n = int(len(data) * 0.8)

  def train_classifier(i):
    print("Training classifier of parameter %d/7" % (i + 1))

    target = list(map(lambda c: c.selected_plan[i], dataset.customers.values()))

    classifier = svm.SVC(gamma=0.01, probability=True)

    print("Training on %d samples." % (n))
    classifier.fit(data[:n], target[:n])
    predicted = classifier.predict(data[n:])
    # print(predicted)
    print("Classifier report for %s:\n%s\n" % (classifier, metrics.classification_report(target[n:], predicted)))
    return classifier

  classifiers = list(map(train_classifier, range(0,7)))
  joblib.dump(classifiers, "trained/svcs.pkl")

if len(sys.argv) > 1 and sys.argv[1] == '--train':
  #train_chosen_browsed_plan()
  train_attribute_classifiers()
else:
  # Load the model.
  scaler = joblib.load("trained/scaler.pkl")
  classifiers = joblib.load("trained/svcs.pkl")
  print("Running.", file=sys.stderr)
  #for pair in pool.map(classify_customer_plan, dataset.customers.values()):
  for pair in map(classify_customer_plan, dataset.customers.values()):
    dataset.customers[pair[0]].selected_plan = pair[1]
  dataset.export_results(sys.stdout)
