import os


def check_utf8_with_bom(path):
    try:
        with open(path, encoding='utf-8') as file:
            lines = file.readlines()
    except UnicodeDecodeError:
        return False
    if lines[0][0] == '\ufeff':
        return True
    return False


def find_bad_files(path):
    bad_files = []
    for root, _, files in os.walk(path):
        for filename in files:
            good_encoding = check_utf8_with_bom(os.path.join(root, filename))
            if good_encoding:
                print(filename + ' is OK')
            else:
                print(filename + ' is badly encoded!')
                bad_files.append(filename)
    print('===== SUMMARY =====')
    if len(bad_files) == 0:
        print('All files are well-formed')
    else:
        print('The list of badly encoded files:')
        print('\n'.join(bad_files))
