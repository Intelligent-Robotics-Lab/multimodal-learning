import xlsxwriter
import collections
from pathlib import Path


def logs2xlsx(logs, output_file):
    workbook = xlsxwriter.Workbook(output_file)
    header_format = workbook.add_format({
        'border': 1,
        'bold': True,
        'text_wrap': True,
        'valign': 'vcenter',
    })
    body_format = workbook.add_format({
        'valign': 'vjustify',
    })
    worksheet = workbook.add_worksheet()
    combined_logs = collections.defaultdict(list)
    for log in logs:
        with open(log, 'r') as f:
            pid = str(log).split('-')[1]
            combined_logs[pid] += f.readlines()

    for pid in sorted(combined_logs.keys()):
        worksheet = workbook.add_worksheet(pid)
        worksheet.set_column('A:B', 30)
        worksheet.set_column('C:D', 20)
        worksheet.write('A1', 'Customer Said', header_format)
        worksheet.write('B1', 'Robot Responded', header_format)
        worksheet.write('C1', 'Robot Should Do', header_format)
        worksheet.write('D1', 'Robot Answer', header_format)
        row = 1
        for line in combined_logs[pid]:
            try:
                robot_utterance = line.split('Robot: ')[1]
                worksheet.write(row, 1, robot_utterance, body_format)
                worksheet.data_validation(row, 2, row, 2, {'validate': 'list',
                                 'source': ['Greeting', 'Checkin', 'Luggage', 'Checkout', 'Amenities', 'Resturants', 'Other'],
                                 })
                worksheet.data_validation(row, 3, row, 3, {'validate': 'list',
                                    'source': ['Appropriate', 'Appropriate w/ ASR error', 'Inappropriate'],
                                    })
                row += 1
                continue
            except IndexError:
                robot_utterance = None
            try:
                user_utterance = line.split('User: ')[1].strip()
                print(f"User utterance '{user_utterance}'")
                user_utterance = '(No response)' if user_utterance == '' else user_utterance
                worksheet.write(row, 0, user_utterance, body_format)
                continue
            except IndexError:
                user_utterance = None
    workbook.close()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--logdir')
    parser.add_argument('-o', '--output-file', default='logs.xlsx')
    args = parser.parse_args()
    logs = Path(args.logdir).glob('*.txt')
    logs2xlsx(logs, args.output_file)