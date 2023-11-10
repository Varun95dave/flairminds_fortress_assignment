import xlrd

xlrd.xlsx.ensure_elementtree_imported(False, None)
xlrd.xlsx.Element_has_iter = True

def read_config(config_file, config_ind, config_pair):

    config_book = xlrd.open_workbook(config_file)

    sheet = config_book.sheet_by_name('Category Lookup')
    n_rows = sheet.nrows

    for colid in range(sheet.ncols):
        hval = sheet.row_values(2)[colid]

        if hval in config_ind.keys():
            for rowid in range(3, n_rows):
                if sheet.row_values(rowid)[colid] != '':
                    config_ind[hval].append(sheet.row_values(rowid)[colid])

        if hval == 'Corresponding Case Type' and sheet.row_values(2)[colid+1] == 'Fortress Damage/Injury':
            for rowid in range(3, n_rows):
                key = sheet.row_values(rowid)[colid]
                value = sheet.row_values(rowid)[colid+1]
                if key not in config_pair['diagnosis_casetype_dict'].keys() and key != '':
                    config_pair['diagnosis_casetype_dict'][key] = [value]
                elif key != '':
                    config_pair['diagnosis_casetype_dict'][key].append(value)

        if hval == 'Corresponding Case Type' and sheet.row_values(2)[colid+1] == 'Defendant':
            for rowid in range(3, n_rows):
                key = sheet.row_values(rowid)[colid]
                value = sheet.row_values(rowid)[colid+1]
                if key not in config_pair['defendent_casetype_dict'].keys() and key != '':
                    config_pair['defendent_casetype_dict'][key] = [value]
                elif key != '':
                    config_pair['defendent_casetype_dict'][key].append(value)
