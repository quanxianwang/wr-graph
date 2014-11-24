#########################################################################
# File Name: fps_collect.sh
# Author: Quanxian Wang <quanxian.wang@intel.com>
#         Wang Lex <lex.wang@intel.com>
# Created Time: Fri 14 Nov 2014 02:33:23 PM CST
#########################################################################
#!/bin/bash
./gui.py --output=output --config=../config/config.xml --log=../log/mine_test/weston5.log --prefix=motion --show=false
./gui.py --output=output --config=../config/config.xml --log=../log/mine_test/weston5.log --prefix=motion --show=true


