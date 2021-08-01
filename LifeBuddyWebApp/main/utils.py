import json
import datetime
from datetime import timedelta
import os, zipfile
import pandas as pd
from flask_login import current_user


def json_dict_to_df_dict(polar_data_dict):
    polar_df_dict={}
    for i,j in polar_data_dict.items():
        if 'training-session-' in i:
            #get utc delta training_session['timeZoneOffset']
            var_datetime_utc=j['timeZoneOffset']
            #get var_datetime_utc LIST
            var_datetime_utc_list=[datetime.datetime.strptime(
                k['dateTime']  ,'%Y-%m-%dT%H:%M:%S.%f') + timedelta(
                    minutes=var_datetime_utc) for k in j['exercises'][0]['samples']['heartRate']]
            #get var_values LIST
            var_values_list=[k['value'] for k in j['exercises'][0]['samples']['heartRate']]
            
            df=pd.DataFrame(list(zip(var_datetime_utc_list,var_values_list)), columns=[
                'var_datetime_utc','var_value'
            ])
            #get var_activity training_session['name']
            df['var_activity']=j['name']
            #get var_periodicity
            df['var_periodicity']='seconds'
            #get vartype = heartrate
            df['var_type']='heart rate'
            #get var_unit 'heart rate per second'
            df['var_unit']='heart rate per second'
            #training_session_df['user_id']=1
            df['user_id']=current_user.id
            #get source_filename = i
            df['source_filename']=i
            df['time_stamp_utc']=datetime.datetime.utcnow()
            df['var_timezone_utc_delta_in_mins']=var_datetime_utc
            polar_df_dict[i]=df
    
    return polar_df_dict