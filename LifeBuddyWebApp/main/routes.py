from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, abort, session,\
    Response, current_app, send_from_directory
from LifeBuddyWebApp import db, bcrypt, mail
from LifeBuddyWebApp.models import User, Variables
from flask_login import login_user, current_user, logout_user, login_required
import secrets
import os
from datetime import datetime, date, time, timedelta
import datetime
from sqlalchemy import func, desc
import pandas as pd
import json
import zipfile
from LifeBuddyWebApp.main.utils import json_dict_to_df_dict


main = Blueprint('main', __name__)

@main.route("/dashboard", methods=["GET","POST"])
@login_required
def dashboard():
    return render_template('dashboard.html')


@main.route("/upload health data", methods=["GET","POST"])
@login_required
def upload_health_data():

    if request.method == 'POST':
        print('POST method')
        formDict = request.form.to_dict()
        filesDict = request.files.to_dict()
        print('formDict:::', formDict)
        print('filesDict:::', filesDict)
        if formDict.get('upload_file_button'):
            print('upload button pressed')
            #save file 
            uploaded_file = request.files['uploaded_file']
            current_files_dir=os.path.join(current_app.config['UPLOADED_FILES_FOLDER'])
            uploaded_file.save(os.path.join(current_files_dir,uploaded_file.filename))
            
            #TODO: polar upload should be a utility of its own. Code should
            #look in json files and pull heart rate by second, distance and speed.
            #right now ***too much hard coded stuff in json_dict_to_df_dict***
            
            #get files to json dict
            polar_zip=zipfile.ZipFile(os.path.join(current_app.config[
                'UPLOADED_FILES_FOLDER'], uploaded_file.filename))
            
            polar_data_dict={}
            for i in polar_zip.filelist:
                polar_data_dict[i.filename]=json.loads(polar_zip.read(i.filename))
            
            
            #get files to df dict
            polar_df_dict=json_dict_to_df_dict(polar_data_dict)
            
            #upload to database
            skip_count=0
            for i,j in polar_df_dict.items():
                if i not in [i[0] for i in db.session.query(Variables.source_filename).all()]:
                    j.to_sql('variables',db.engine,if_exists='append', index=False)
                else:
                    skip_count+=1
            
            print('skip_count:::',skip_count)
            
            flash(f'Files uploaded', 'success')
            return redirect(url_for('main.upload_health_data'))
            
            
            
    
    return render_template('upload_health_data.html')
    
    
    
    
    
    
    