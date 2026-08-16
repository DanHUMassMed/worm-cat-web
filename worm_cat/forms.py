import flask
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, RadioField, TextAreaField, DecimalField, SubmitField, BooleanField, IntegerField, HiddenField, PasswordField
from wtforms.validators import DataRequired, Regexp, Optional

from decimal import Decimal
import re
import string


class WormCatForm(FlaskForm):
    name = StringField('name', validators=[DataRequired("Name is required.")])
    email = StringField('email', validators=[DataRequired("Email is required.")])
    title = StringField('title', validators=[DataRequired("Title is required.")])

    annotation_choices = [('whole_genome_v2', 'Whole genome v2'),
                          ('ORF_only_v2', 'ORF only v2'),
                          ('ahringer_v2','Ahringer RNAi v2'),
                          ('orfeome_v2','Orfeome RNAi v2'),
                          ('whole_genome_v1','Whole genome v1'),
                          ('ahringer_v1','Ahringer v1'),
                          ('orfeome_v1','Orfeome v1')]
    annotation_type = SelectField('annotation_type', coerce=str, choices=annotation_choices)

    input_type_choices = [('Sequence.ID', 'Sequence ID'), ('Wormbase.ID', 'Wormbase ID')]
    input_type = SelectField('input_type', coerce=str, choices=input_type_choices)

    rgs = TextAreaField('rgs', validators=[DataRequired("Regulated Gene Expression list is required.")])
    # submit = SubmitField('Submit')

class AdminForm(FlaskForm):
    pass

class LoginForm(FlaskForm):
    user_name = StringField('user_name', validators=[DataRequired("Username is required.")])
    password = PasswordField('password', validators=[DataRequired("Password is required.")])
    submit = SubmitField('Sign In')

class BatchForm(FlaskForm):
    email = HiddenField('email')
    xsl_file_nm = HiddenField('xsl_file_nm')
    batch_user = HiddenField('batch_user')
    annotation_file = HiddenField('annotation_file')

    submit_wait = SubmitField('Wait')
    submit_email = SubmitField('Email')



