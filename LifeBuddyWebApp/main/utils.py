import json
import datetime
from datetime import timedelta
import os, zipfile
import pandas as pd
from flask_login import current_user
from LifeBuddyWebApp import db, bcrypt, mail
from LifeBuddyWebApp.models import User, Post, Health_description, Health_measure
from sqlalchemy import func
from scipy.optimize import curve_fit
import numpy as np

from bokeh.plotting import figure, output_file
from bokeh.embed import components
from bokeh.resources import CDN
from bokeh.io import curdoc
from bokeh.themes import built_in_themes
from bokeh.models import ColumnDataSource, Grid, LinearAxis, Plot, Text
import pytz
import zoneinfo
from pytz import timezone

def plot_text_format(x):
    return ('%.1f' % x).rstrip('0').rstrip('.')

#The model set to max heartrate = 170
def michaelis_m_eq_fix170(time_var, shape_var):
    return (170 *time_var)/(shape_var + time_var)

def json_dict_to_dfs(polar_data_dict):

    df_description=pd.DataFrame()
    df_measure=pd.DataFrame()
    max_id=db.session.query(func.max(Health_description.id)).first()[0]
    
    #TODO if lenghth is less than 140 then drop
    for i,j in polar_data_dict.items():
        if 'training-session-' in i:
            #get last id from database
            max_id=1 if max_id==None else max_id +1
            df1=pd.DataFrame()
            
            df1['var_activity']=[j['exercises'][0]['sport']]#if one row, first should be in brackets or soemthing liek that
            df1['var_type']='heart rate'#must come from input data polar h1 only does heart rate
            df1['var_periodicity']='seconds' #must come from input data polar h1 only does seconds
            df1['var_timezone_utc_delta_in_mins']=j['exercises'][0]['timezoneOffset']
            df1['time_stamp_utc']=datetime.datetime.utcnow()
            df1['user_id']=current_user.id#comes from app current_user.id
            df1['source_filename']=i
            df1['description_id']=max_id
            df1['datetime_of_activity']=datetime.datetime.strptime(j['startTime'],'%Y-%m-%dT%H:%M:%S.%f')

            var_datetime_utc_list=[]
            for data_item_series in j['exercises'][0]['samples']:
                if data_item_series!='recordedRoute' and len(var_datetime_utc_list)==0:
                    var_datetime_utc_list=[datetime.datetime.strptime(
                        x['dateTime'],'%Y-%m-%dT%H:%M:%S.%f')+ timedelta(
                        minutes=j['exercises'][0]['timezoneOffset']) for x in j[
                        'exercises'][0]['samples'][data_item_series]]

                    df2=pd.DataFrame(var_datetime_utc_list,columns=['var_datetime_utc'])
                    df2['description_id']=max_id
                    reading_count=len(var_datetime_utc_list)
                if data_item_series== 'heartRate':
                    df2['heart_rate']=[x['value'] for x in j['exercises'][0]['samples'][data_item_series]]
                if data_item_series== 'speed':
                    df2['speed']= [x['value'] for x in j['exercises'][0]['samples'][data_item_series]]
                if data_item_series== 'distance':
                    df2['distance']= [x['value'] for x in j['exercises'][0]['samples'][data_item_series]]
                if data_item_series== 'recordedRoute':
                    longitude_list= [x['longitude'] for x in j['exercises'][0]['samples'][data_item_series]]
                    while reading_count>len(longitude_list):
                        longitude_list.append(longitude_list[-1])
                    df2['longitude']=longitude_list
                    latitude_list= [x['latitude'] for x in j['exercises'][0]['samples'][data_item_series]]
                    while reading_count>len(latitude_list):
                        latitude_list.append(latitude_list[-1])
                    df2['latitude']=latitude_list
                    altitude_list= [x['altitude'] for x in j['exercises'][0]['samples'][data_item_series]]
                    while reading_count>len(altitude_list):
                        altitude_list.append(altitude_list[-1])
                    df2['altitude']=altitude_list
            
            df1['metric2_session_duration']=reading_count
            
            df_description=df_description.append(df1, ignore_index = True)
            df_measure=df_measure.append(df2, ignore_index = True)
    df_description.set_index('description_id', inplace=True)
    
    #calculate metric1_cardio
    metric1_list=[]
    for description_id in df_measure['description_id'].unique():
        df_byId=df_measure[df_measure.description_id==description_id]
        x_obs=df_byId.var_datetime_utc.to_list()
        if len(x_obs)>139:
            x_obs=[(i-x_obs[0]).total_seconds() for i in x_obs][:140]
            y_obs=df_byId.heart_rate.to_list()[:140]
            popt_fix170 = curve_fit(michaelis_m_eq_fix170, x_obs, y_obs,bounds=(0,np.inf))[0][0]
        else:
            popt_fix170=np.nan
        metric1_list.append(popt_fix170)

    #add metric1_cardio to df_description
    df_description['metric1_carido']=metric1_list
    
    ####Check that same polar time stamps are not uploaded.
    #get existing database health_measure.description id and var_datetime_utc ***TODO Make this filter on user*****
    base_query_health_measure=db.session.query(Health_measure.description_id,Health_measure.var_datetime_utc)
    health_measure_var_datetime=pd.read_sql(str(base_query_health_measure),db.session.bind) 
    health_measure_var_datetime.rename(columns={'health_measure_description_id':'description_id',
                                               'health_measure_var_datetime_utc':'var_datetime_utc'}, inplace=True)

    if len(health_measure_var_datetime)>0:
        ##convert both var_datetime_utc columns to string
        df_measure_2=df_measure
        df_measure_2.var_datetime_utc=df_measure_2.var_datetime_utc.astype(str)    

        #check that var_datetime_utc is same length as in df_measure
        if len(health_measure_var_datetime.var_datetime_utc[0])>len(df_measure_2.var_datetime_utc[0]):
            cut_length=(len(health_measure_var_datetime.var_datetime_utc[0])-len(df_measure_2.var_datetime_utc[0]))*-1
            health_measure_var_datetime.var_datetime_utc=health_measure_var_datetime.var_datetime_utc.str[:cut_length]
        if len(df_measure_2.var_datetime_utc[0])>len(health_measure_var_datetime.var_datetime_utc[0]):
            cut_length=(len(df_measure_2.var_datetime_utc[0])-len(health_measure_var_datetime.var_datetime_utc[0]))*-1
            df_measure_2.var_datetime_utc=df_measure_2.var_datetime_utc.str[:cut_length]

        df_matching_times=pd.merge(df_measure_2, health_measure_var_datetime,on="var_datetime_utc")
        dup_descript_id_list=list(df_matching_times.description_id_x.unique())
        
        #overwrite upload dataframes with duplicate training sessions removed.
        df_measure=df_measure[~df_measure.description_id.isin(dup_descript_id_list)]
        df_description=df_description[~df_description.index.isin(dup_descript_id_list)]
    
    return (df_description,df_measure)
    

def chart_scripts(df_health_description):
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
    p2=figure(x_axis_label='Time',x_axis_type='datetime',width=880, height=400, toolbar_location=None,
              tools='xwheel_zoom,xpan',active_scroll='xwheel_zoom',x_range=(date_start, date_end))
    p2.yaxis.major_label_text_color='black'

    glyph = Text(text="text", text_color="#d6fbf7")

    p2.add_glyph(source, glyph)


    script1, div1 = components(p2, theme='night_sky')

    return (script1, div1)






