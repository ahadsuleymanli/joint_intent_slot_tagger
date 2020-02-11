This is a self contained web service for Goo format data labelling.
The format is specified in Slot-Gated Modeling for Joint Slot Filling and Intent Prediction (Goo et al):
B-[slotname] I-[slotname] O
data is stored in seq.in, seq.out, label files one line per text sample

What you need:
- Python 3.6
- pip for Python 3.6
- pipenv (pip install --user pipenv)

How to run:
1. clone the repository
2. cd joint_intent_slot_tagger
3. pipenv install
4. pipenv shell
5. cd mysite
6. python manage.py runserver
7. open http://127.0.0.1:8000/index/ in your browser
