# 超簡易Backburner Submitterスクリプト
# IFDを所定のフォルダに出力した後に、backburnerに投げたいROP(mantraのみ）を選んでこのツールを実行
# 各ROPのIFDの場所を読んでコマンドを生成してジョブを投げる
# 生成したコマンドやタスクファイルは、$HIP/dispatch以下に格納され、それが実行されるという流れ
# 基本的にはShelfに登録して使う想定
# priorityやserversなどはROP側に新規でparm追加して読むなどすればROP側での調整も可能だが未対応

import hou
import os
import os.path
import re
import subprocess

version = hou.applicationVersionString()
mantra = r'C:\Program Files\Side Effects Software\Houdini {}\bin\mantra.exe'.format(version)
manager = 'manager_name'
#servers = '-servers rendermachine001, rendermachine002'
servers = '-group "mantra"'
priority = '-priority 50'
port = '7347'
tmpl = 'cmdjob -jobname {jobname} -manager {manager} -port {port} {priority} {servers} -taskList "{taskfile}" -taskname 1 "{mantra}" -f %%tp2 -v 2pa'

def gen_taskfile(path, taskfile_dir):
    if not os.path.isdir(path):
        raise ValueError('{0} is not a valid directory.'.format(path))

    ptn = re.compile('.+\.ifd')
    items = sorted([item for item in os.listdir(path) if ptn.match(item)])
    _, dirname = os.path.split(path)

    taskfile = '{0}\\task_{1}.txt'.format(taskfile_dir, dirname)
    nitems = len(items)

    with open(taskfile, 'w') as f:
        for i, item in enumerate(items):
            fullpath = '{0}\\{1}'.format(path, item)
            line = '[Mantra] {0} of {1}\t{2}\n'.format(i+1, nitems, fullpath)
            f.write(line)
    return nitems, taskfile

def main(root_dir, ifd_dir):
    taskfile_dir = '{}\\taskfiles'.format(root_dir)
    bat_dir = '{}\\bat'.format(root_dir)
    for d in [taskfile_dir, bat_dir]:
        if not os.path.isdir(d):
            os.makedirs(d)
            print('[Make Directory] {}'.format(d))
    nfiles, taskfile = gen_taskfile(ifd_dir, taskfile_dir)
    jobname = ifd_dir.split('\\')[-1]
    kwds = {'jobname': jobname, 'manager': manager, 'port': port, 'priority': priority, 'servers': servers, 'taskfile': taskfile, 'mantra': mantra}
    command = tmpl.format(**kwds)
    batname = '{}\\exec_{}.bat'.format(bat_dir, jobname)
    with open(batname, 'w') as f:
        f.write(command)
        #f.write('\r\npause')
    cmd = 'cmd /c "{}"'.format(batname)
    print(subprocess.check_output(cmd))

# Start here
mantra_nodes = [o for o in hou.selectedNodes() if o.type().name() == 'ifd']
root_dir = os.path.normpath('{}\\dispatch'.format(hou.getenv('HIP')))
if not os.path.isdir(root_dir):
    os.makedirs(root_dir)
    print('[Make Directory] {}'.format(root_dir))
ifd_dirs = [os.path.normpath(os.path.dirname(m.parm('soho_diskfile').eval())) for m in mantra_nodes]
for ifd_dir in ifd_dirs:
    if not os.path.isdir(ifd_dir):
        print('[Warning] Directory not found: {}'.format(ifd_dir))
    main(root_dir, ifd_dir)
print('# Done')
