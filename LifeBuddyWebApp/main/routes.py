from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, abort, session,\
    Response, current_app, send_from_directory
from LifeBuddyWebApp import db, bcrypt, mail
from LifeBuddyWebApp.models import User, Post, Health_description, Health_measure
from flask_login import login_user, current_user, logout_user, login_required
import secrets
import os
from datetime import datetime, date, time, timedelta
import datetime
from sqlalchemy import func, desc
import pandas as pd
import json
import zipfile
from LifeBuddyWebApp.main.utils import json_dict_to_dfs, plot_text_format, chart_scripts
from bokeh.plotting import figure, output_file
from bokeh.embed import components
from bokeh.resources import CDN
from bokeh.io import curdoc
from bokeh.themes import built_in_themes
from bokeh.models import ColumnDataSource, Grid, LinearAxis, Plot, Text
import pytz
import zoneinfo
from pytz import timezone
import time

main = Blueprint('main', __name__)



@main.route("/dashboard", methods=["GET","POST"])
@login_required
def dashboard():
    
    user_record=db.session.query(User).filter(User.id==current_user.id).first()
    user_tz=user_record.user_timezone
    
    user_tz = timezone(user_tz)
    default_date=datetime.datetime.now().astimezone(user_tz).strftime("%Y-%m-%d")
    default_time=datetime.datetime.now().astimezone(user_tz).strftime("%H:%M")
    
    #filter on user data only
    base_query_health_description=db.session.query(Health_description).filter(Health_description.user_id==1)
    
    if current_user.id==2:
        df_health_description=pd.read_sql(str(base_query_health_description)[:-1]+str(1),db.session.bind)
    else:
        df_health_description=pd.read_sql(str(base_query_health_description)[:-1]+str(current_user.id),db.session.bind)
    
    if len(df_health_description)>0:
        script1, div1=chart_scripts(df_health_description)
        cdn_js=CDN.js_files
        cdn_css=CDN.css_files
    else:
        div1=None;script1=None;cdn_js=None;cdn_css=None

    #Timle line table
    df_sub=df_health_description[['id', 'datetime_of_activity', 'var_activity','metric1_carido']].copy()
    df_sub=df_sub.sort_values(by='datetime_of_activity', ascending=False)
    df_sub.datetime_of_activity=df_sub['datetime_of_activity'].astype('datetime64[ns]')
    df_sub.datetime_of_activity=pd.to_datetime(df_sub["datetime_of_activity"].dt.strftime('%m/%d/%Y %H:%M'))
    table_lists=df_sub.values.tolist()
    for i in table_lists:
        if i[3]=='nan':
            print('fire')
            i[3]='not exercise'
        else:
            i[3]='{0:.3g}'.format(i[3])
        
    
    if len(table_lists)==0:
        no_hits_flag=True
    else:
        no_hits_flag=False

    if request.method == 'POST':
        formDict = request.form.to_dict()
        print('formDcit::::',formDict)
        if formDict.get('submit_activity'):
            #convert this date time to utc
            date_time_obj_unaware = datetime.datetime.strptime(formDict.get('activity_date')+formDict.get('activity_time'), '%Y-%m-%d%H:%M')
            date_time_obj_aware=user_tz.localize(date_time_obj_unaware)
            timezone_offset = date_time_obj_aware.utcoffset().total_seconds()/60
            
            var_activity=formDict.get('var_activity')
            activity_notes=formDict.get('activity_notes')
            metric3=formDict.get('metric3')
            
            return redirect(url_for('main.add_activity', date_time_obj_aware=date_time_obj_aware,timezone_offset=timezone_offset))

        elif formDict.get('submit_upload_health'):
            return redirect(url_for('main.upload_health_data'))
    
    return render_template('dashboard.html', div1=div1, script1=script1, cdn_js=cdn_js, cdn_css=cdn_css,
        default_date=default_date, default_time=default_time, table_data=table_lists, no_hits_flag=no_hits_flag,
        len=len)


@main.route("/add_activity",methods=["GET","POST"])
@login_required
def add_activity():
    print('requests:::',request.args)
    date_time_obj_aware=request.args('date_time_obj_aware')
    print('date_time_obj_aware:::::', date_time_obj_aware)
    
    # var_timezone_utc_delta_in_mins get this by using the: cur_zone_time.utcoffset().total_seconds()/60
    if formDict.get('metric3'):
        update_activity=Health_description(datetime_of_activity=date_time_obj_aware,var_activity=var_activity,var_type='Activity',
            var_timezone_utc_delta_in_mins=timezone_offset, metric3=formDict.get('metric3'), user_id=current_user.id,
            source_filename='web application')
    else:
        update_activity=Health_description(datetime_of_activity=date_time_obj_aware,var_activity=var_activity,var_type='Activity',
            var_timezone_utc_delta_in_mins=timezone_offset, user_id=current_user.id,
            source_filename='web application')
    db.session.add(update_activity)
    db.session.commit()
    return redirect(url_for('main.dashboard'))
    # return render_template('dashboard.html', div1=div1, script1=script1, cdn_js=cdn_js, cdn_css=cdn_css,
        # default_date=default_date, default_time=default_time)



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
            # print(dir(filesDict.get('uploaded_file')))
            # print('filename:::',filesDict.get('uploaded_file').filename)
            if filesDict.get('uploaded_file').filename=='':
                flash(f'File not selected', 'warning')
                return redirect(url_for('main.upload_health_data'))
                
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
            df_description,df_measure=json_dict_to_dfs(polar_data_dict)
            
            
            #put data into tables
            df_description.to_sql('health_description',db.engine, if_exists='append',index=False)
            df_measure.to_sql('health_measure',db.engine, if_exists='append',index=False)
            
            flash(f'Files uploaded', 'success')
            return redirect(url_for('main.upload_health_data'))
            
            
            
    
    return render_template('upload_health_data.html')
    
    
    
    
    
    
    