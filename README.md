# A self contained web service for Goo format data labelling.<br/>
The format is specified in the paper `Slot-Gated Modeling for Joint Slot Filling and Intent Prediction (Goo et al)`.<br/>
#### Features:
- Add new intent labels and slots on the fly!
- Add, delete, edit intents.
- Exporting dataset in form of seq.in, seq.out, label text files.
#### Demo:
![](https://media.giphy.com/media/kH6OHJa0fa6JnneFKy/giphy.gif)
#### What you need:</br>
- Python 3.6
- pip for Python 3.6
- pipenv ( ```pip install --user pipenv``` )

#### How to run:
1. clone the repository
2. ```cd joint_intent_slot_tagger```
3. ```pipenv install```
4. ```pipenv shell```
5. ```cd mysite```
6. ```python manage.py runserver```
7. open http://127.0.0.1:8000/index/ in your browser

