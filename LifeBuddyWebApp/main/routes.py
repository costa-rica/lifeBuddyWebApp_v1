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
from LifeBuddyWebApp.main.utils import json_dict_to_dfs, plot_text_format
from bokeh.plotting import figure, output_file
from bokeh.embed import components
from bokeh.resources import CDN
from bokeh.io import curdoc
from bokeh.themes import built_in_themes
from bokeh.models import ColumnDataSource, Grid, LinearAxis, Plot, Text

main = Blueprint('main', __name__)



@main.route("/dashboard", methods=["GET","POST"])
@login_required
def dashboard():

    base_query_health_description=db.session.query(Health_description)
    df_health_description=pd.read_sql(str(base_query_health_description),db.session.bind)
    
    colNames=[i[len('health_description_'):] for i in list(df_health_description.columns)]
    col_names_dict={i:j for i,j in zip(list(df_health_description.columns),colNames)}
    df_health_description.rename(columns=col_names_dict, inplace=True)
    
    df1=df_health_description.loc[df_health_description.metric1_carido<100]
    df1=df1.sort_values(by=['datetime_of_activity'])
    x_obs=[ datetime.datetime.strptime(date_string,'%Y-%m-%d %H:%M:%S.%f') for date_string in df1.datetime_of_activity]
    y_obs=df1.metric1_carido
    y_obs_formatted=[ plot_text_format(i) for i in y_obs]


    date_end=datetime.datetime.strptime(df1.datetime_of_activity.to_list()[-1],'%Y-%m-%d %H:%M:%S.%f')
    date_end=date_end+ timedelta(days=1)
    date_start=date_end- timedelta(days=7)

    
    source = ColumnDataSource(dict(x=x_obs, y=y_obs, text=y_obs_formatted))
    p2=figure(x_axis_label='Time',x_axis_type='datetime',y_axis_label='your life data',width=880, height=300, toolbar_location=None,
              tools='xwheel_zoom,xpan',active_scroll='xwheel_zoom',x_range=(date_start, date_end))
    p2.yaxis.major_label_text_color='black'

    glyph = Text(text="text", text_color="#d6fbf7")

    p2.add_glyph(source, glyph)
   
    
    script1, div1 = components(p2, theme='night_sky')
    
    print('div1:::',div1)
    
    cdn_js=CDN.js_files
    cdn_css=CDN.css_files
    

    return render_template('dashboard.html', div1=div1, script1=script1, cdn_js=cdn_js, cdn_css=cdn_css)


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
    
    
    
    
    
    
    