import os
import re
import math
import xlrd
import datetime
from fuzzywuzzy import process as pcs
import pandas as pd

def parse_filename(filename,conf_ind):

    file_text = filename.split("_")

    lf_borrower = pcs.extractOne(file_text[0].split("/")[-1][5:], conf_ind['Fortress Counsel Law Firm'])[0]

    report_date = datetime.datetime.strptime(file_text[-1].split('.')[0], '%d-%m-%Y').strftime('%Y-%b-%d')

    return lf_borrower, report_date

def parse_date_format(obj):
    if type(obj) == float:
        try:
            date = xlrd.xldate_as_datetime(obj, 0).strftime('%Y-%b-%d')
        except:
            return f'flag: date incorrect- {obj}'

    return date

def map_case_type(obj, mapper):

    rec = pcs.extractOne(obj, mapper)[0]

    return rec

def parse_diagnosis_text(text, rowid, dem, data, mapper):

    rec_lst = []
    map = mapper[data['case_type'][rowid-1]]

    if dem in text:
        lst = text.split(dem)
        for elm in lst:
            rec_lst.append(map_case_type(elm,map))
    else:
        rec_lst.append(map_case_type(text, map))

    return rec_lst



def extract(filename, sheetname, data, conf_ind, conf_pairs):

    law_firm_borrower, report_date = parse_filename(filename, conf_ind)


    work_book = xlrd.open_workbook(filename)
    sheet = work_book.sheet_by_name(sheetname)
    n_cols = sheet.ncols
    n_rows = sheet.nrows
    print(f"In {law_firm_borrower} file, {sheetname} sheet has {n_rows} rows and {n_cols} columns")


    for colid in range(n_cols):
        hval = sheet.row_values(0)[colid]

        # 'Project ID' ---> cross check if any curation required -- truncate decimal for int
        if (hval == 'Project Number' or hval == 'Project ID'):
            for rowid in range(1, n_rows):
                data['case_number'].append(sheet.row_values(rowid)[colid])

        # 'Create Date' ---> flaot -- parse_date_format -- '%Y-%b-%d'
        if hval == 'Create Date':
            for rowid in range(1, n_rows):
                data['client_retained_date'].append(parse_date_format(sheet.row_values(rowid)[colid]))

        # 'Product Used?' ---> producing case_type and defendant
        if hval == 'Product Used?':
            for rowid in range(1, n_rows):
                cell_value = sheet.row_values(rowid)[colid]
                if (cell_value != '' or type(cell_value) != float or cell_value != ' ') :
                    rec_value = map_case_type(cell_value, conf_ind['Fortress Case Type'])
                else:
                    rec_value = map_case_type(sheetname, conf_ind['Fortress Case Type'])
                data['case_type'].append(rec_value)
                data['defendant'].append(conf_pairs['defendent_casetype_dict'][rec_value][0])


        #   Conditional derived attributes based on Phase field
        if hval == 'Phase':
            for rowid in range(1, n_rows):
                cell_value = sheet.row_values(rowid)[colid]
                if cell_value == 'Settled':
                    data["settled_or_not_settled?"].append('Yes')
                    data["filed_or_not_filed_?"].append('No')
                    data["closed_or_not_closed?"].append('No')
                elif cell_value == 'Litigation':
                    data["settled_or_not_settled?"].append('No')
                    data["filed_or_not_filed_?"].append('Yes')
                    data["closed_or_not_closed?"].append('No')
                elif cell_value == 'Terminated':
                    data["settled_or_not_settled?"].append('No')
                    data["filed_or_not_filed_?"].append('No')
                    data["closed_or_not_closed?"].append('Yes')
                else:
                    data["settled_or_not_settled?"].append('No')
                    data["filed_or_not_filed_?"].append('No')
                    data["closed_or_not_closed?"].append('No')

        #   Conditional derived attributes based on 'Count of Medical Records Items' field, **certain wbk don't have this field
        if hval == 'Count of Medical Records Items':
            for rowid in range(1, n_rows):
                cell_value = sheet.row_values(rowid)[colid]
                if cell_value != 0:
                    data["medical_record_present_or_not_present?"].append('Yes')
                else:
                    data["medical_record_present_or_not_present?"].append('No')

        # Borrower Share of Fee
        if hval == 'PW % Percentage':
            for rowid in range(1, n_rows):
                cv = sheet.row_values(rowid)[colid]
                if type(cv) == float:
                    data["borrower_share_of_fee"].append(f"{cv}%")
                elif (type(cv) == str and "/" in cv):
                    c = re.findall("\d+\.\d+",cv)
                    data["borrower_share_of_fee"].append(f"{c[0]}%")
                elif type(cv) == str and "%" in cv:
                    data["borrower_share_of_fee"].append(f"{float(cv[:-1])}%")
                else:
                    data["borrower_share_of_fee"].append(f"0%")

        # --Co-Counsel % Percentage
        if hval == 'Co-Counsel % Percentage':
            for rowid in range(1, n_rows):
                cv = sheet.row_values(rowid)[colid]
                if type(cv) == float:
                    data["co-counsel_%_percentage"].append(f"{cv}%")
                elif type(cv) == str and "/" in cv:
                    c = cv.split("/")[0]
                    data["co-counsel_%_percentage"].append(f"{c}%")
                elif type(cv) == str and "%" in cv:
                    data["co-counsel_%_percentage"].append(f"{float(cv[:-1])}%")
                else:
                    data["co-counsel_%_percentage"].append(f"0%")

        # Damage/InjuryX fields based on Diagnosis and Case Type
        if hval == 'Diagnosis':
            for rowid in range(1, n_rows):
                cv = sheet.row_values(rowid)[colid]
                cv_lst = []
                if type(cv) == str:
                    for delimiter in [',',';','and']:
                        cv_lst += parse_diagnosis_text(cv, rowid, delimiter, data, conf_pairs['diagnosis_casetype_dict'])
                    cv_lst = list(set(cv_lst))
                    if len(cv_lst) == 3:
                        data['damage_injury_1'].append(cv_lst[0])
                        data['damage_injury_2'].append(cv_lst[1])
                        data['damage_injury_3'].append(cv_lst[2])
                    elif  len(cv_lst) == 2:
                        data['damage_injury_1'].append(cv_lst[0])
                        data['damage_injury_2'].append(cv_lst[1])
                        data['damage_injury_3'].append('-')
                    elif  len(cv_lst) == 1:
                        data['damage_injury_1'].append(cv_lst[0])
                        data['damage_injury_2'].append('-')
                        data['damage_injury_3'].append('-')
                    else:
                        data['damage_injury_1'].append(f"flag: more than 3 diagnosis recorded {cv_lst}")
                        data['damage_injury_2'].append(f"flag: more than 3 diagnosis recorded {cv_lst}")
                        data['damage_injury_3'].append(f"flag: more than 3 diagnosis recorded {cv_lst}")
                else:
                    data['damage_injury_1'].append(f"flag: data received as {type(cv)}, {cv}")
                    data['damage_injury_2'].append(f"flag: data received as {type(cv)}, {cv}")
                    data['damage_injury_3'].append(f"flag: data received as {type(cv)}, {cv}")

        # Preparing co-counsel law firm's list
        if hval == 'PW & Co-Counsel':
            for rowid in range(1, n_rows):
                cell_value = sheet.row_values(rowid)[colid]
                if type(cell_value) == str and cell_value.count('&') > 0:
                    result = re.split('&', cell_value)
                    rlst = [pcs.extractOne(i, conf_ind['Fortress Counsel Law Firm']) if len(
                        i) > 3 else '' for i in result]
                    rlst2 = list(set([j[0] if (type(j) == tuple and j[1]>85 and j[0] != 'Law Firm 1') else '' for j in rlst]))
                    rlst2.sort(key=len, reverse=True)
                    data['co_counsel_firm_names'].append(rlst2)
                else:
                    data['co_counsel_firm_names'].append("flag: PW & [law firm] or [law firm] & PW pattern not found")



    data["report_date"] = [report_date]*(n_rows-1)
    data["law_firm_borrower"] = [law_firm_borrower]*(n_rows-1)

    if len(data["medical_record_present_or_not_present?"]) == 0:
        data["medical_record_present_or_not_present?"] = ['']*(n_rows-1)

    # data["co_counsel_1_share_of_fee"] =
    # data["co-counsel_2_share_of_fee"] =
    # data["co-counsel_3_share_of_fee"] =
    # data["co-counsel_4_share_of_fee"] =
    # data["co-counsel_5_share_of_fee"] =

    return 'abc'

def feature_extraction(data):

    cc1_fnm = []
    cc2_fnm = []
    cc3_fnm = []
    cc4_fnm = []
    cc5_fnm = []

    for firms in data['co_counsel_firm_names']:
        if type(firms) == list:
            l = len(firms)
            for i in range(5):
                if i < l:
                    exec(f"cc{i+1}_fnm.append(firms[{i}])")
                else:
                    exec(f"cc{i+1}_fnm.append('')")
        else:
            for i in range(5):
                exec(f"cc{i + 1}_fnm.append('')")


    data['co_counsel_1_name'] = cc1_fnm
    data['co_counsel_2_name'] = cc2_fnm
    data['co_counsel_3_name'] = cc3_fnm
    data['co_counsel_4_name'] = cc4_fnm
    data['co_counsel_5_name'] = cc5_fnm

    hlm_list = []

    for brw, co, lf1, co1 in zip(data['borrower_share_of_fee'],data['co-counsel_%_percentage'],data['law_firm_borrower'],data['co_counsel_1_name']):
        brw = float(brw[:-1])
        co = float(co[:-1])
        if brw >= co:
            hlm_list.append(lf1)
        else:
            hlm_list.append(co1)

    data["handling_law_firm"] = hlm_list

    data["co_counsel_1_share_of_fee"] = data['co-counsel_%_percentage']

    data.drop(columns = ['co_counsel_firm_names','co-counsel_%_percentage'], inplace=True)

    data = get_unique_latest_record(data)

    return data

def get_unique_latest_record(data):

    subset_col = ['case_number','client_retained_date','case_type',
                'settled_or_not_settled?','filed_or_not_filed_?','closed_or_not_closed?','borrower_share_of_fee',
                'damage_injury_1','damage_injury_2','damage_injury_3','defendant',
                'co_counsel_1_name','co_counsel_2_name','co_counsel_3_name','co_counsel_4_name',
                'co_counsel_5_name','handling_law_firm','co_counsel_1_share_of_fee']

    data2 = data.sort_values(by=['report_date'], ascending=False).reset_index(drop = True)

    data2 = data2.drop_duplicates(subset=subset_col)


    return data2