import sys
import time

code = sys.argv[1]
log_out = open('../../../All/m_' + code + '/output/tutorial_1.log', 'w')
log_err = open('../../../All/m_' + code + '/output/tutorial_1.err', 'w')
sys.stdout = log_out
sys.stderr = log_err
print("you are running the merger with code: "+code)
time.sleep(20)
error
