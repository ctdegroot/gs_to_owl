# Gradescope to OWL Tool

## Purpose

The purpose of this tool is to convert downloaded grades from Gradescope to a format that can be imported to OWL, the learning management system used at Western University.

## Usage

To use, you must first download your grades from Gradescope. To do this, navigate to the "Assignments" tab of your course. Then, click "Download Grades". Then, go to OWL and download your Gradebook. To do this, navigate to the "Gradebook" tab of your course, then go to "Import / Export". From this page, click "Export Gradebook".

Next you have to fill out the configuration file, which is in JSON format. An example is found in the `examples` folder of this repository.

The first sub-dictionary in the configuration file, `grading_scheme`, defines the overall grading scheme for the course, where each item may have two or more subitems. If an item in `grading_scheme` has no subitems, then the name must match exactly with the name used on Gradescope. The values must add to 100.

The next sub-dictionary is `subitems`. There must be an entry for each of the items in `grading_scheme`. If there are subitems, a list is given, where the names match the Gradescope assignment names. If there are no subitems, a value of `false` is listed.

The next sub-dictionary is `drop_lowest`, which specifies `true` if the lowest value of the subitems is to be dropped or `false` if all subitems are to be kept. For items without subitems, a value of `false` must be specified.

The next sub-dictionary is `excused`, which defines any deliverables where a student has been excused. All empty entries are given a value of zero, except for those listed in the `excused` sub-dictionary. The format of this sub-dictionary is a student ID (username) as a key and a list of deliverables from which they are excused as a value.

The final sub-dictionary is `replace_if_better`. This defines any deliverables that should be replaced if the grade on another deliverable is better. This is meant to be applied to top-level items and not subitems. The individual subitem grades are not changed by the replacement function; it is only the aggregated grade that is replaced. The example file gives the replacement `"Tests" : "Final Exam"`. In this case, "Tests" is made up of two individual tests, but the value will be replaced if "Final Exam" is higher. The grades of each test will be unchanged.

Once all of these files are in place, the script is run as follows:

```
python gs_to_owl.py --gs <path to gradescope file> --owl <path to owl file> --config <path to config file>
```

The script will output two files into the working directory. The first is `gs_output.csv`, which includes all data including intermediate values and the calculation of the course grade. The second is `owl_output.csv` which can be imported into OWL. The OWL file contains all of the subitems as well as the aggreggated grades for each category. It is recommended to only select "Include item in course grade calculations?" for the grade categories and not the individual subitems. If this is done, the calculated grade in OWL will match exactly with the one reported in `gs_output.csv`.

## Contributing

If you have contributions, feature requests, or bug reports, use the Github Issues tool.

## License

This software is licensed under the MIT License.
