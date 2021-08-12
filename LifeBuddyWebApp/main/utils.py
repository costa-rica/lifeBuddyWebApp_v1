import json
import datetime
from datetime import timedelta
import os, zipfile
import pandas as pd
from flask_login import current_user
from LifeBuddyWebApp import db, bcrypt, mail
from LifeBuddyWebApp.models import User, Post, Health_description, Health_measure
from sqlalchemy import func


def json_dict_to_df_dict(polar_data_dict):
    polar_df_dict1={}
    polar_df_dict2={}
    max_id=db.session.query(func.max(Health_description.id)).first()[0]
    for i,j in polar_data_dict.items():
        if 'training-session-' in i:
            for data_item in j['exercises'][0]['samples'].keys():
                # print('current training session data item: ', data_item)
                if data_item != 'recordedRoute':
                    if max_id==None:
                        max_id=1
                    else:
                        max_id +=1
                    df1=pd.DataFrame()
                    df1['id']=[max_id]
                    df1['var_activity']=[j['name']]
                    df1['var_type']=['heart rate']
                    df1['var_periodicity']=['seconds']
                    df1['var_unit']=['heart rate per second']
                    df1['var_timezone_utc_delta_in_mins']=[j['timeZoneOffset']]
                    df1['time_stamp_utc']=[datetime.datetime.utcnow()]
                    df1['user_id']=[1]#replace with current user
                    df1['source_filename']=[i]
                    polar_df_dict1[i]=df1
                
                    var_datetime_utc=j['timeZoneOffset']
                    var_datetime_utc_list=[datetime.datetime.strptime(
                        k['dateTime']  ,'%Y-%m-%dT%H:%M:%S.%f') + timedelta(
                            minutes=var_datetime_utc) for k in j['exercises'][0]['samples']['heartRate']]
                    var_values_list=[k['value'] for k in j['exercises'][0]['samples']['heartRate']]
                    df2=pd.DataFrame(list(zip(var_datetime_utc_list,var_values_list)), columns=[
                        'var_datetime_utc','var_value'])
                    df2['description_id']=max_id
                    polar_df_dict2[i]=df2
                
                
                
                    ##**stuff that comes from the data***
                    # var_datetime_utc=j['timeZoneOffset']
                    # var_datetime_utc_list=[datetime.datetime.strptime(
                        # k['dateTime']  ,'%Y-%m-%dT%H:%M:%S.%f') + timedelta(
                            # minutes=var_datetime_utc) for k in j['exercises'][0]['samples'][data_item]]
                    # var_values_list=[k['value'] for k in j['exercises'][0]['samples'][data_item]]
                    # df=pd.DataFrame(list(zip(var_datetime_utc_list,var_values_list)), columns=[
                        # 'var_datetime_utc','var_value'])
                    # df['var_activity']=j['name']
                    # df['user_id']=current_user.id
                    # df['source_filename']=i            
                    # df['time_stamp_utc']=datetime.datetime.utcnow()
                    # df['var_timezone_utc_delta_in_mins']=var_datetime_utc
                    
                    ##**stuff that comes from the data***
                    ##get var_periodicity
                    #df['var_periodicity']='seconds'
                    ##get vartype = heartrate
                    #df['var_type']=data_item
                    ##get var_unit 'heart rate per second'
                    #df['var_unit']=data_item + ' per second'
                    ##training_session_df['user_id']=1
                    #print('counted ' + str(len(var_values_list)) + 'in ', data_item )

                    #polar_df_dict[i]=df
    
    return (polar_df_dict1,polar_df_dict2)