# autogcode
Get stl file from mail, slice it and put in uploads folder in octoprint.
Then update your google spreadsheet with the new input.
The script will only get the files that meet the search criteria in config.ini.
Also Slic3r commands can be passed in the subject.

The autogcode.py is based on https://gist.github.com/jasonrdsouza/1674794 work, i just change it to my needs and updated some code.

The gsinput.py is a modification of the sample code given by Google https://developers.google.com/sheets/api/quickstart/python
