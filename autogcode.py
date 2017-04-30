import email
import imaplib
import os
import re
import time
import datetime
import subprocess
from dateutil.parser import parse
from configparser import ConfigParser, ExtendedInterpolation
from gsinput import main

cfg = 'configs.ini'  # absolute cfg path


# taking care of configuration so this file is not so crowded
config = ConfigParser(interpolation=ExtendedInterpolation())
config.read(cfg)
config = config['CFG']

# connecting to IMAP
m = imaplib.IMAP4_SSL(host=config.get('imap'), port=config.get('port'))
m.login(config.get('user'), config.get('pwd'))

while int(config.get('timer')) > 0:
    m.select()  # selecting INBOX

    # UNSEEN = not read FROM my domain TEXT with the text
    resp, items = m.search(None, config.get('search'))
    items = items[0].split()  # email ID

    for emailid in items:
        resp, data = m.fetch(emailid, "(RFC822)")  # RFC822 = all
        email_body = data[0][1].decode('utf-8')  # getting the mail content
        mail = email.message_from_string(email_body)  # mail object
        # Check if any attachments at all
        if mail.get_content_maintype() != 'multipart':
            continue

        email_from = mail["From"]
        fr = re.split(r"(\s)", email_from)
        email_from = fr[0] + " " + fr[2]  # using to get First Last name
        email_subject = mail["Subject"]  # to get extra config for slic3r

        for part in mail.walk():
            # multipart are just containers, so we skip them
            if part.get_content_maintype() == 'multipart':
                continue

            # is this part an attachment ?
            if part.get('Content-Disposition') is None:
                continue

            now = datetime.datetime.strftime(
                parse(mail["Date"]),
                '%d%m%Y%H%M%S'
            )
            filename = now
            filename = re.sub('([\-\s\:\+])|(0000)', '', filename)
            stlfilename = filename + ".stl"
            filename = filename + ".gcode"
            att_path = os.path.join(config.get('adir'), stlfilename)
            update_googlesheet = {
                'range': 'A1:C500',
                'values': [
                    [
                        str(email_from),
                        str(filename),
                        datetime.datetime.strftime(
                            parse(mail["Date"]),
                            '%d/%m/%Y,%H:%M:%S'
                        )
                    ]
                ],
                'majorDimension': 'ROWS'
            }
            main(update_googlesheet)

            # writing file to disk
            if not os.path.isfile(att_path):
                fp = open(att_path, 'wb')
                fp.write(part.get_payload(decode=True))
                fp.close()

                # using regular expression to get extra options for slic3r
                mo = re.compile(r"(--\S*\s(?!--)\S*)|(--\S*)")
                mopt = mo.findall(email_subject)
                # loading configuration file and building options
                nmopt = " --load " + config.get('slconf')
                for t in mopt:
                    g1, g2 = t
                    if g1 and not g2:
                        nmopt = nmopt + " " + g1
                    elif g2 and not g1:
                        nmopt = nmopt + " " + g2
                    else:
                        continue

                # slicing
                stlfile_opt = att_path + nmopt
                subprocess.Popen([
                                 '/bin/bash',
                                 config.get('slic3r'),
                                 stlfile_opt]).communicate()
                os.remove(att_path)  # remove stl file
    m.close()
    time.sleep(int(config.get('timer')))
