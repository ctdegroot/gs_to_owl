import pandas as pd
import numpy as np
import argparse
import json

def read_config(file):
    with open(file) as json_file:
        return json.load(json_file)

def read_gradescope(file):
    # Read Gradescope file
    gs = pd.read_csv(file)

    # Filter out columns related to timing/lateness
    gs = gs[gs.columns[~gs.columns.str.contains('- Submission|- Lateness|Total Lateness')]]

    # Return the dataframe
    return gs

def read_owl(file):
    # Read the OWL Gradebook, retaining only the student information
    owl = pd.read_csv(file)
    owl = owl[['Student ID', 'Name', '# Student Number']]

    # Return the dataframe
    return owl

def fill_zeros(gs, config):
    # Get relevant configuration data
    excused = config['excused']

    # Fill all null values with zeros
    gs = gs.fillna(0)

    # Revert any items that are excused
    for sid, item in excused.items():
        idx = gs[gs['SID'].str.match(sid)].index[0]
        gs.loc[idx, item] = np.nan

    # Return dataframe
    return gs

def add_subitem_averages(gs, config):
    # Get relevant configuration data
    grading_scheme = config['grading_scheme']
    subitems = config['subitems']
    drop_lowest = config['drop_lowest']

    # Loop through all categories with subitems
    for item, subs in subitems.items():
        # Case for items with subitems
        if subs:
            # Get the column names for the value of each item
            max_points = ['{} - Max Points'.format(x) for x in subs]

            # Sum all of the subitems
            gs[item] = gs[subs].sum(axis=1)

            # Get the points for each item (NOTE: this assumes they are equal value)
            gs['{} - Max Points'.format(item)] = gs[max_points].mean(axis=1)

            # Get the number of non-null subitems
            gs['{} - Non-Null'.format(item)] = len(subs) - gs[subs].isnull().sum(axis=1)

            # Case where lowest value is dropped
            if drop_lowest[item]:
                # Save the lowest value
                gs['{} - Lowest'.format(item)] = gs[subs].min(axis=1)

                # Subtract value from sum
                gs[item] = gs[item] - gs['{} - Lowest'.format(item)]

                # Subtract 1 from the non-null items
                gs['{} - Non-Null'.format(item)] = gs['{} - Non-Null'.format(item)] - 1

            # Calculate grade for this item
            gs[item] = gs[item]/(gs['{} - Max Points'.format(item)]*gs['{} - Non-Null'.format(item)])
            gs[item] = gs[item]*grading_scheme[item]

        # Case for items without subitems
        else:
            gs[item] = gs[item]/gs['{} - Max Points'.format(item)]*grading_scheme[item]

        # Round calculated values to 2 decimal places
        gs[item] = gs[item].round(decimals=2)

        # Replace max points with value of this item
        gs['{} - Max Points'.format(item)] = grading_scheme[item]

    # Return dataframe
    return gs

def replace_grades(gs, config):
    # Get relevant configuration data
    replace_if_better = config['replace_if_better']

    # Loop through item replacements
    for item, replacement in replace_if_better.items():
        # Identify items to be replaced
        label = 'Override {} with {}?'.format(item, replacement)
        gs[label] = gs[replacement]/gs['{} - Max Points'.format(replacement)] > gs[item]/gs['{} - Max Points'.format(item)]

        # Do replacement
        gs.loc[gs[label], item] = gs[replacement]/gs['{} - Max Points'.format(replacement)]*gs['{} - Max Points'.format(item)]

        # Round values to 2 decimal places
        gs[item] = gs[item].round(decimals=2)

    # Return dataframe
    return gs

def calculate_course_grade(gs, config):
    # Get relevant configuration data
    grading_scheme = config['grading_scheme']

    # Sum items in grading scheme
    gs['Course Grade'] = gs[grading_scheme.keys()].sum(axis=1)

    # Return dataframe
    return gs

def sort_gs(gs, config):
    # Get relevant configuration data
    subitems = config['subitems']
    drop_lowest = config['drop_lowest']
    replace_if_better = config['replace_if_better']

    # Define column ordering
    order = ['First Name', 'Last Name', 'SID', 'Email', 'Sections']
    for item, subs in subitems.items():
        if subs:
            for sub in subs:
                order += [sub, '{} - Max Points'.format(sub)]
            if drop_lowest[item]:
                order += ['{} - Lowest'.format(item)]
            order += ['{} - Non-Null'.format(item)]

        order += [item, '{} - Max Points'.format(item)]
    for item, replacement in replace_if_better.items():
        order += ['Override {} with {}?'.format(item, replacement)]
    order += ['Course Grade']

    # Reorder the dataframe
    gs = gs[order]

    # Return dataframe
    return gs

def merge_owl_gs(owl, gs, config):
    # Get relevant configuration data
    subitems = config['subitems']

    # Store the column names for adding point value later
    columns = []

    # Merge all items into OWL dataframe
    for item, subs in subitems.items():
        # Merge subitems
        if subs:
            owl = owl.merge(gs[['SID'] + subs], left_on='Student ID', right_on='SID')
            owl = owl.drop('SID', axis=1)
            columns += subs

        # Merge main items
        owl = owl.merge(gs[['SID', item]], left_on='Student ID', right_on='SID')
        owl = owl.drop('SID', axis=1)
        columns += [item]


    # Rename columns to include max points
    for col in columns:
        value = gs.loc[0, '{} - Max Points'.format(col)]
        owl = owl.rename(columns={col : '{} [{}]'.format(col, int(value))})

    # Return dataframe
    return owl

# Set up command line arguments
arg_parser = argparse.ArgumentParser(description='Convert Gradescope file to OWL Gradebook.')
arg_parser.add_argument('--gs', help='Gradescope input file', type=str, nargs=1, required=True)
arg_parser.add_argument('--owl', help='OWL input file', type=str, nargs=1, required=True)
arg_parser.add_argument('--config', help='Configuation file', type=str, nargs=1, required=True)
args = arg_parser.parse_args()

# Run the script
config = read_config(args.config[0])
gs = read_gradescope(args.gs[0])
owl = read_owl(args.owl[0])
gs = fill_zeros(gs, config)
gs = add_subitem_averages(gs, config)
gs = replace_grades(gs, config)
gs = calculate_course_grade(gs, config)
gs = sort_gs(gs, config)
owl = merge_owl_gs(owl, gs, config)
gs.to_csv('gs_output.csv', index=False)
owl.to_csv('owl_output.csv', index=False)
