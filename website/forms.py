from wtforms import Form, SubmitField
from flask_wtf import FlaskForm

class PurchaseItemForm(FlaskForm):
    submit = SubmitField(label = 'Purchase Item!')


class SellItemForm(FlaskForm):
    submit = SubmitField(label = 'Sell Item!')