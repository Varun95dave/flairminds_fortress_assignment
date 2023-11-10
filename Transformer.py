import os
import sys
import glob
import pandas as pd
import openpyxl
import xlrd
import numpy as np
import extract_data
import read_config

xlrd.xlsx.ensure_elementtree_imported(False, None)
xlrd.xlsx.Element_has_iter = True

class Transformer:
    def __init__(self, *args, **kwargs):

        super().__init__()

        self.data = {"report_date": [],
                    "law_firm_borrower": [],
                    "case_number": [],
                    "client_retained_date": [],
                    "case_type": [],
                    "settled_or_not_settled?": [],
                    "filed_or_not_filed_?": [],
                    "closed_or_not_closed?": [],
                    "medical_record_present_or_not_present?": [],
                    "borrower_share_of_fee": [],
                    "damage_injury_1": [],
                    "damage_injury_2": [],
                    "damage_injury_3": [],
                    "defendant": [],
                    "co-counsel_%_percentage": [],
                    "co_counsel_firm_names": []}

                    # "co-counsel_1_share_of_fee": [],
                    # "co-counsel_2_share_of_fee": [],
                    # "co-counsel_3_share_of_fee": [],
                    # "co-counsel_4_share_of_fee": [],
                    # "co-counsel_5_share_of_fee": []
                    #                      }

        self.conf_ind = {'Fortress Damage/Injury':[],
                         'Defendant':[],
                         'Fortress Case Type':[],
                         'Fortress Counsel Law Firm':[]}

        self.conf_pairs = {'diagnosis_casetype_dict':{},'defendent_casetype_dict':{}}

        self.input_folderpath = "C:/Users/HP/Documents/Varun/Entrepreneur/flairminds/Input/"
        self.config_file = "C://Users//HP//Documents//Varun//Entrepreneur//flairminds//Fortress Master Tape.xlsx"
        self.output_filepath = "C://Users//HP//Documents//Varun//Entrepreneur//flairminds//flair.csv"

    def get_files(self):

        xlsx_files = [f for f in glob.glob(self.input_folderpath + "*.xlsx", recursive=True)]

        return xlsx_files

    def get_files_df(self):

        files = self.get_files()

        final_df = pd.DataFrame()

        for file in files:
            workbook = xlrd.open_workbook(file)
            all_sheets = workbook.sheet_names()
            print(file)
            for idx, sheets in enumerate(all_sheets):
                first_call = extract_data.extract(file, sheets, self.data, self.conf_ind, self.conf_pairs)
                data_df = pd.DataFrame(self.data)
                final_df = final_df.append(data_df)

                for key, value in self.data.items():
                    self.data[key] = []

        final_df = extract_data.feature_extraction(final_df)

        return final_df



    def transform(self):

        read_config.read_config(self.config_file, self.conf_ind,self.conf_pairs)

        final_df = self.get_files_df()

        final_df.to_csv(self.output_filepath, sep=',', header=True, index=False)
